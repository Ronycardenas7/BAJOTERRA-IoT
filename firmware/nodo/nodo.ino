/* ==================================================================
   BAJOTERRA · ESP32 NODO  (versión 3.0 final – igual para los 3 módulos)
   ================================================================== */
#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_idf_version.h>
#include <DHT.h>

#define ZONA_ID 1                  // 1 = ÁRIDO · 2 = TEMPLADO (húmedo) · 3 = SELVÁTICO

const int CAL_SECO     = 3500;
const int CAL_SATURADO = 1500;

uint8_t MAC_MAESTRO[6] = {0xE8, 0x9F, 0x6D, 0xB6, 0x8D, 0x3C};
const char* WIFI_SSID = "S24 FE Rony";

#define PIN_DHT        4
#define PIN_SUELO     34
#define PIN_SUELO_VCC 25
#define DHTTYPE    DHT22

const uint32_t PERIODO_MS = 2000;
const int      MUESTRAS   = 10;
const float    ALFA       = 0.3f;
const uint8_t  FALLOS_PARA_CAMBIAR_CANAL = 3;
const uint8_t  FALLOS_PARA_BUSCAR_ROUTER = 15;

typedef struct __attribute__((packed)) {
  uint8_t  zona_id;
  uint32_t seq;
  float    temp_c;
  float    hr_aire;
  uint16_t suelo_raw;
  float    suelo_pct;
  uint8_t  flags;
} Paquete;

DHT dht(PIN_DHT, DHTTYPE);
Paquete paq;
uint8_t canal = 1;
bool hayRouter = false;
volatile uint8_t fallosSeguidos = 0;
float sueloFiltrado = NAN;
uint32_t ultimoEnvio = 0;

void fijarCanal(uint8_t ch) {
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
}

uint8_t buscarCanalRouter() {
  int n = WiFi.scanNetworks();
  uint8_t ch = 0;
  for (int i = 0; i < n; i++) {
    if (WiFi.SSID(i) == WIFI_SSID) { ch = WiFi.channel(i); break; }
  }
  WiFi.scanDelete();
  return ch;
}

#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 0)
void alEnviar(const wifi_tx_info_t* info, esp_now_send_status_t estado) {
#else
void alEnviar(const uint8_t* mac, esp_now_send_status_t estado) {
#endif
  if (estado == ESP_NOW_SEND_SUCCESS) fallosSeguidos = 0;
  else fallosSeguidos = fallosSeguidos + 1;
}

int leerSueloCrudo() {
  digitalWrite(PIN_SUELO_VCC, HIGH);
  delay(100);
  long suma = 0;
  for (int i = 0; i < MUESTRAS; i++) {
    suma += analogRead(PIN_SUELO);
    delay(5);
  }
  digitalWrite(PIN_SUELO_VCC, LOW);
  return suma / MUESTRAS;
}

float crudoAPorcentaje(int crudo) {
  float pct = (float)(CAL_SECO - crudo) * 100.0f / (float)(CAL_SECO - CAL_SATURADO);
  return constrain(pct, 0.0f, 100.0f);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_SUELO_VCC, OUTPUT);
  digitalWrite(PIN_SUELO_VCC, LOW);
  analogReadResolution(12);
  dht.begin();

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  uint8_t ch = buscarCanalRouter();
  hayRouter = (ch > 0);
  canal = hayRouter ? ch : 1;
  fijarCanal(canal);

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error iniciando ESP-NOW. Reiniciando...");
    delay(2000);
    ESP.restart();
  }
  esp_now_register_send_cb(alEnviar);

  esp_now_peer_info_t par = {};
  memcpy(par.peer_addr, MAC_MAESTRO, 6);
  par.channel = 0;
  par.ifidx   = WIFI_IF_STA;
  par.encrypt = false;
  esp_now_add_peer(&par);

  paq.zona_id = ZONA_ID;
  paq.seq = 0;
  Serial.printf("NODO zona %d iniciado. Canal %d. Mi MAC: %s\n",
                ZONA_ID, canal, WiFi.macAddress().c_str());
  Serial.printf("Enviando al maestro: %02X:%02X:%02X:%02X:%02X:%02X\n",
                MAC_MAESTRO[0], MAC_MAESTRO[1], MAC_MAESTRO[2],
                MAC_MAESTRO[3], MAC_MAESTRO[4], MAC_MAESTRO[5]);
}

void loop() {
  if (millis() - ultimoEnvio < PERIODO_MS) return;
  ultimoEnvio = millis();

  float t = dht.readTemperature();
  float h = dht.readHumidity();
  bool dhtOk = !isnan(t) && !isnan(h);

  int crudo = leerSueloCrudo();
  bool sueloOk = crudo > 20;
  if (sueloOk) {
    float pct = crudoAPorcentaje(crudo);
    sueloFiltrado = isnan(sueloFiltrado) ? pct : ALFA * pct + (1.0f - ALFA) * sueloFiltrado;
  }

  paq.seq++;
  paq.temp_c    = dhtOk ? t : 0;
  paq.hr_aire   = dhtOk ? h : 0;
  paq.suelo_raw = crudo;
  paq.suelo_pct = (sueloOk && !isnan(sueloFiltrado)) ? sueloFiltrado : 0;
  paq.flags     = (dhtOk ? 0x01 : 0) | ((sueloOk && !isnan(sueloFiltrado)) ? 0x02 : 0);
  esp_now_send(MAC_MAESTRO, (uint8_t*)&paq, sizeof(paq));

  if (hayRouter && fallosSeguidos >= FALLOS_PARA_CAMBIAR_CANAL) {
    canal = (canal % 13) + 1;
    fijarCanal(canal);
    fallosSeguidos = 0;
    Serial.printf("Maestro no responde: probando canal %d\n", canal);
  }
  else if (!hayRouter && fallosSeguidos >= FALLOS_PARA_BUSCAR_ROUTER) {
    uint8_t ch = buscarCanalRouter();
    if (ch > 0) { hayRouter = true; canal = ch; Serial.printf("Router encontrado: canal %d\n", canal); }
    fijarCanal(canal);
    fallosSeguidos = 0;
  }

  Serial.printf("Zona %d | #%lu | T=%.1f C  HR=%.0f %% | suelo crudo=%d -> %.0f %% | canal %d | %s | %s %s\n",
                ZONA_ID, (unsigned long)paq.seq, t, h, crudo, paq.suelo_pct, canal,
                fallosSeguidos == 0 ? "MAESTRO OK" : "SIN RESPUESTA",
                dhtOk ? "" : "[ERROR DHT22]", sueloOk ? "" : "[ERROR FC-28]");
}
