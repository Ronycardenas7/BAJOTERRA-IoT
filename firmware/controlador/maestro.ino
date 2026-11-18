/* ==================================================================
   BAJOTERRA · ESP32 MAESTRO  (versión 3.0 – ESP-NOW + pantalla táctil + Supabase)
   ------------------------------------------------------------------
   Qué hace:
     · Recibe los datos de los 3 nodos por ESP-NOW (inalámbrico).
     · VENTILADOR: PI sobre la temperatura (ventanas de 30 s, mín. 2 s).
     · RIEGO: pulsos con banda (histéresis) y ALARMA si los pulsos no sirven.
     · PANTALLA CYD por cable: G17 → IO22 (datos) · G16 ← IO27 (órdenes táctiles).
     · NUBE: sube las lecturas a Supabase (RPC registrar_lectura) cada 30 s
             y revisa órdenes de la web (comandos_pendientes) cada 5 s.
   Sin Wi-Fi todo el control sigue igual (la nube es opcional).
   Núcleo 1 = CONTROL · Núcleo 0 = RED
   Librería: "ArduinoJson" (v7). Ya NO se usa PubSubClient (MQTT).
   ================================================================== */
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_random.h>
#include <esp_arduino_version.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <time.h>
#include <sys/time.h>

// Credenciales privadas fuera de Git (archivo secretos.h ignorado por Git).
#include "secretos.h"

#ifndef ESP_ARDUINO_VERSION_MAJOR
#define ESP_ARDUINO_VERSION_MAJOR 2
#endif

// ===================== 1. CONFIGURACIÓN (referenciada desde secretos.h) =====================
const char* WIFI_SSID         = WIFI_SSID_VAL;
const char* WIFI_PASS         = WIFI_PASS_VAL;

// --- Supabase (referenciada desde secretos.h y web_pwa/src/config/nube.js) ---
const char* SUPABASE_URL      = SUPABASE_URL_VAL;   // sin "/" al final
const char* SUPABASE_KEY      = SUPABASE_KEY_VAL;   // la key pública de la web
const char* CLAVE_DISPOSITIVO = CLAVE_DISPOSITIVO_VAL; // clave del controlador
const char* DISPOSITIVO_ID    = DISPOSITIVO_ID_VAL;

// --- Nombres que usan tus funciones RPC: coinciden con las migraciones Supabase ---
const char* CABECERA_CLAVE   = "x-device-key";
const char* FN_LECTURA       = "registrar_lectura";
const char* ARG_LECTURA      = "";
const char* FN_PENDIENTES    = "comandos_pendientes";
const char* ARG_PEND_DISP    = "";
const char* FN_CONFIRMAR     = "confirmar_comando";
const char* ARG_CONF_ID      = "p_id";
const char* ARG_CONF_RES     = "";
const char* VALOR_CONF_RES   = "ejecutado";
const char* CALIDAD_BUENA    = "buena";
const char* CALIDAD_MALA     = "mala";

// ===================== 2. PINES =====================
#define RXD2 16              // ← IO27 de la pantalla CYD (órdenes táctiles)
#define TXD2 17              // → IO22 de la pantalla CYD (datos)
#define RELE_ON  LOW         // tus módulos: LOW enciende
#define RELE_OFF HIGH

// ===================== 3. TIEMPOS Y LÍMITES GENERALES =====================
const uint32_t PERIODO_PID_MS      = 2000;
const float    DT_S                = PERIODO_PID_MS / 1000.0f;
const uint32_t TIMEOUT_DATO_MS     = 15000;
const uint32_t PERIODO_PANTALLA_MS = 2000;
const uint32_t PERIODO_SUBIDA_MS   = 30000;
const uint32_t PERIODO_ORDENES_MS  = 5000;
const uint32_t MANUAL_WEB_MS       = 120000;
const uint32_t VENTANA_VENT_MS     = 30000;
const uint32_t MIN_ON_VENT_MS      = 2000;
const float    KP_VENT             = 30.0f;
const float    KI_VENT             = 0.15f;
const float    SUBIDA_MIN_SUELO    = 3.0f;
const uint8_t  PULSOS_SIN_EFECTO   = 3;
const uint8_t  MAX_PULSOS_CICLO    = 10;
const uint32_t MANUAL_BOMBA_MAX_MS = 30000;
const uint32_t ESPERA_WIFI_MS      = 10000;
const uint32_t REINTENTO_WIFI_MS   = 120000;
const uint8_t  CANAL_RESPALDO      = 1;
const float    SIN_DATO            = -99.0f;

// ===================== 4. PAQUETE (idéntico al del nodo) =====================
typedef struct __attribute__((packed)) {
  uint8_t  zona_id;
  uint32_t seq;
  float    temp_c;
  float    hr_aire;
  uint16_t suelo_raw;
  float    suelo_pct;
  uint8_t  flags;
} Paquete;

// ===================== 5. ESTRUCTURAS =====================
struct Ventilador {
  uint8_t  pin;
  float    uMax;
  float    I, u, uFijo;
  uint32_t tOnMs;
  int32_t  ventanaActual;
  uint32_t desfaseMs;
  bool     encendido;
};

struct Riego {
  uint8_t  pin;
  uint32_t pulsoMs, esperaMs;
  bool     encendido;
  bool     ciclo;
  bool     huboPulso;
  uint32_t tInicioPulso, tFinPulso;
  float    sueloRef;
  uint8_t  sinEfecto, pulsosCiclo;
  bool     alarma;
};

struct Zona {
  const char* nombre;
  const char* key;
  char        letra;
  Ventilador  vent;
  Riego       riego;
  float spTemp;
  float spMin, spMax;
  float sueloMin, sueloMax;
  float hrMin, hrMax;
  bool  limitaVentPorHR;
  bool  manual, manBomba, manVent;
  uint32_t manBombaDesde;
  uint32_t manualHasta;
  float    temp, hr, suelo;
  uint32_t seq, perdidos, ultimoDatoMs;
  bool     tieneDato, enLinea;
};

const int NZ = 3;
Zona zonas[NZ];

// ===================== 6. RECURSOS COMPARTIDOS ENTRE NÚCLEOS =====================
SemaphoreHandle_t mutexZonas;
portMUX_TYPE muxBuffer = portMUX_INITIALIZER_UNLOCKED;
Paquete bufferPaq[NZ];
bool    hayNuevo[NZ] = {false, false, false};
volatile uint32_t rxTotal = 0;
volatile int      rxUltimoLen = 0;

Preferences  prefs;

volatile bool     wifiConectado = false, horaOk = false;
volatile uint32_t subidasOk = 0, subidasFallidas = 0, ordenesWeb = 0;

bool valido(float x) { return x > SIN_DATO + 1.0f; }

void configurarZona(Zona& z, const char* nombre, const char* key, char letra,
                    float spT, float sMin, float sMax, float hMin, float hMax, bool limita,
                    uint8_t pinVent, float uMaxVent, uint32_t desfaseS,
                    uint8_t pinBomba, uint32_t pulsoS, uint32_t esperaMin) {
  z.nombre = nombre; z.key = key; z.letra = letra;
  z.spTemp = spT; z.spMin = spT - 5.0f; z.spMax = spT + 5.0f; z.sueloMin = sMin; z.sueloMax = sMax; z.hrMin = hMin; z.hrMax = hMax;
  z.limitaVentPorHR = limita;
  z.manual = false; z.manBomba = false; z.manVent = false; z.manBombaDesde = 0; z.manualHasta = 0;
  z.temp = SIN_DATO; z.hr = SIN_DATO; z.suelo = SIN_DATO;
  z.seq = 0; z.perdidos = 0; z.ultimoDatoMs = 0; z.tieneDato = false; z.enLinea = false;

  Ventilador& V = z.vent;
  V.pin = pinVent; V.uMax = uMaxVent; V.desfaseMs = desfaseS * 1000;
  V.I = 0; V.u = 0; V.uFijo = 0; V.tOnMs = 0; V.ventanaActual = -1; V.encendido = false;

  Riego& R = z.riego;
  R.pin = pinBomba; R.pulsoMs = pulsoS * 1000; R.esperaMs = esperaMin * 60000UL;
  R.encendido = false; R.ciclo = false; R.huboPulso = false;
  R.tInicioPulso = 0; R.tFinPulso = 0; R.sueloRef = 0;
  R.sinEfecto = 0; R.pulsosCiclo = 0; R.alarma = false;
}

void configurarZonas() {
  configurarZona(zonas[0], "arida",     "A", 'A', 24.0f, 15.0f, 35.0f, 20.0f, 40.0f, false,
                 33, 100.0f,  0,   25, 5, 15);
  configurarZona(zonas[1], "humeda",    "H", 'H', 22.0f, 30.0f, 50.0f, 40.0f, 60.0f, false,
                 26, 100.0f, 10,   27, 4, 10);
  configurarZona(zonas[2], "selvatica", "S", 'S', 25.0f, 40.0f, 60.0f, 55.0f, 75.0f, true,
                 14, 100.0f, 20,   13, 4, 10);
}

void clave(char* out, const Zona& z, char var) { sprintf(out, "%s_%c", z.key, var); }

void cargarObjetivos() {
  char k[8];
  for (int i = 0; i < NZ; i++) {
    Zona& z = zonas[i];
    clave(k, z, 't'); z.spTemp   = constrain(prefs.getFloat(k, z.spTemp), z.spMin, z.spMax);
    clave(k, z, 'a'); z.sueloMin = prefs.getFloat(k, z.sueloMin);
    clave(k, z, 'b'); z.sueloMax = prefs.getFloat(k, z.sueloMax);
  }
}

void guardarObjetivos(int i) {
  char k[8];
  clave(k, zonas[i], 't'); prefs.putFloat(k, zonas[i].spTemp);
  clave(k, zonas[i], 'a'); prefs.putFloat(k, zonas[i].sueloMin);
  clave(k, zonas[i], 'b'); prefs.putFloat(k, zonas[i].sueloMax);
}

#if ESP_ARDUINO_VERSION_MAJOR >= 3
void alRecibir(const esp_now_recv_info_t* info, const uint8_t* datos, int len) {
#else
void alRecibir(const uint8_t* mac, const uint8_t* datos, int len) {
#endif
  rxTotal = rxTotal + 1;
  rxUltimoLen = len;
  if (len != sizeof(Paquete)) return;
  Paquete p;
  memcpy(&p, datos, sizeof(p));
  if (p.zona_id < 1 || p.zona_id > NZ) return;
  portENTER_CRITICAL(&muxBuffer);
  bufferPaq[p.zona_id - 1] = p;
  hayNuevo[p.zona_id - 1] = true;
  portEXIT_CRITICAL(&muxBuffer);
}

void fijarCanal(uint8_t ch) {
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
}

void tomarPaquetes(uint32_t ahora) {
  for (int i = 0; i < NZ; i++) {
    Paquete p;
    bool nuevo = false;
    portENTER_CRITICAL(&muxBuffer);
    if (hayNuevo[i]) { p = bufferPaq[i]; hayNuevo[i] = false; nuevo = true; }
    portEXIT_CRITICAL(&muxBuffer);
    if (!nuevo) continue;

    Zona& z = zonas[i];
    if (z.tieneDato && p.seq > z.seq + 1) z.perdidos += p.seq - z.seq - 1;
    z.seq   = p.seq;
    z.temp  = (p.flags & 0x01) ? p.temp_c    : SIN_DATO;
    z.hr    = (p.flags & 0x01) ? p.hr_aire   : SIN_DATO;
    z.suelo = (p.flags & 0x02) ? p.suelo_pct : SIN_DATO;
    z.ultimoDatoMs = ahora;
    z.tieneDato = true;
  }
}

void reiniciarVent(Ventilador& V) { V.I = 0; V.u = 0; V.tOnMs = 0; V.ventanaActual = -1; }

float calcularPI(Ventilador& V, float T, float Tobj, float uMaxEf) {
  float e = T - Tobj;
  if (e <= 0.0f) { V.I = 0.0f; return 0.0f; }
  V.I = constrain(V.I + KI_VENT * e * DT_S, 0.0f, uMaxEf);
  return constrain(KP_VENT * e + V.I, 0.0f, uMaxEf);
}

bool enVentana(Ventilador& V, uint32_t ahora) {
  if (ahora < V.desfaseMs) return false;
  uint32_t t = ahora - V.desfaseMs;
  int32_t idx = t / VENTANA_VENT_MS;
  uint32_t pos = t % VENTANA_VENT_MS;
  if (idx != V.ventanaActual) {
    V.ventanaActual = idx;
    V.uFijo = V.u;
    V.tOnMs = (uint32_t)(V.uFijo / 100.0f * VENTANA_VENT_MS);
    if (V.tOnMs < MIN_ON_VENT_MS) V.tOnMs = 0;
  }
  return pos < V.tOnMs;
}

void reiniciarRiego(Riego& R) { R.ciclo = false; R.huboPulso = false; R.sinEfecto = 0; R.pulsosCiclo = 0; }

void pasarAAuto(Zona& z) {
  z.manual = false; z.manBomba = false; z.manVent = false; z.manualHasta = 0;
  z.riego.alarma = false; reiniciarRiego(z.riego);
}

bool otraBombaEncendida(const Riego* yo) {
  for (int i = 0; i < NZ; i++)
    if (&zonas[i].riego != yo && zonas[i].riego.encendido) return true;
  return false;
}

bool gestionarRiego(Zona& z, uint32_t ahora) {
  Riego& R = z.riego;

  if (R.encendido) {
    if (ahora - R.tInicioPulso < R.pulsoMs) return true;
    R.tFinPulso = ahora;
    return false;
  }
  if (!z.enLinea || !valido(z.suelo)) { reiniciarRiego(R); return false; }

  if (R.alarma) {
    if (z.suelo >= z.sueloMin) { R.alarma = false; Serial.printf("Zona %s: alarma de riego despejada\n", z.nombre); }
    else return false;
  }

  if (!R.ciclo) {
    if (z.suelo >= z.sueloMin) return false;
    R.ciclo = true; R.huboPulso = false; R.sinEfecto = 0; R.pulsosCiclo = 0;
    Serial.printf("Zona %s: suelo %.0f%% < %.0f%% -> inicia riego\n", z.nombre, z.suelo, z.sueloMin);
  }

  if (z.suelo >= z.sueloMax) {
    Serial.printf("Zona %s: suelo %.0f%% >= %.0f%% -> fin del riego (%d pulsos)\n",
                  z.nombre, z.suelo, z.sueloMax, R.pulsosCiclo);
    reiniciarRiego(R);
    return false;
  }

  if (R.huboPulso && ahora - R.tFinPulso < R.esperaMs) return false;

  if (R.huboPulso) {
    if (z.suelo - R.sueloRef >= SUBIDA_MIN_SUELO) R.sinEfecto = 0;
    else R.sinEfecto++;
    if (R.sinEfecto >= PULSOS_SIN_EFECTO || R.pulsosCiclo >= MAX_PULSOS_CICLO) {
      R.alarma = true;
      reiniciarRiego(R);
      Serial.printf("ALARMA RIEGO zona %s: los pulsos no suben el suelo (revisar sonda, agua o bomba)\n", z.nombre);
      return false;
    }
  }

  if (otraBombaEncendida(&R)) return false;

  R.sueloRef = z.suelo;
  R.tInicioPulso = ahora;
  R.huboPulso = true;
  R.pulsosCiclo++;
  Serial.printf("Zona %s: pulso de riego %d (%lu s)\n", z.nombre, R.pulsosCiclo, (unsigned long)(R.pulsoMs / 1000));
  return true;
}

int estadoRiego(const Zona& z) { return z.riego.encendido ? 1 : (z.riego.ciclo ? 2 : 0); }

void calcularZona(Zona& z, uint32_t ahora) {
  bool antes = z.enLinea;
  z.enLinea = z.tieneDato && (ahora - z.ultimoDatoMs <= TIMEOUT_DATO_MS);
  if (antes && !z.enLinea) Serial.printf("ALARMA: zona %s sin datos (>15 s)\n", z.nombre);
  if (!antes && z.enLinea) Serial.printf("Zona %s en linea\n", z.nombre);

  if (!z.enLinea || z.manual) { reiniciarVent(z.vent); return; }

  if (valido(z.temp)) {
    float uMaxV = z.vent.uMax;
    if (z.limitaVentPorHR && valido(z.hr) && z.hr < z.hrMin) uMaxV = min(uMaxV, 25.0f);
    z.vent.u = calcularPI(z.vent, z.temp, z.spTemp, uMaxV);
  } else reiniciarVent(z.vent);
}

void escribirPin(uint8_t pin, bool& estado, bool on) {
  if (estado == on) return;
  digitalWrite(pin, on ? RELE_ON : RELE_OFF);
  estado = on;
}

void actualizarReles(uint32_t ahora) {
  for (int i = 0; i < NZ; i++) {
    Zona& z = zonas[i];
    bool quiereV, quiereB;

    if (z.manual && z.manualHasta && (int32_t)(ahora - z.manualHasta) >= 0) {
      pasarAAuto(z);
      Serial.printf("Zona %s: fin de los 2 min de orden web -> AUTO\n", z.nombre);
    }
    if (z.manual) {
      if (z.manBomba && ahora - z.manBombaDesde > MANUAL_BOMBA_MAX_MS) {
        z.manBomba = false;
        Serial.printf("Zona %s: bomba manual apagada por tiempo\n", z.nombre);
      }
      quiereV = z.manVent;
      quiereB = z.manBomba && !otraBombaEncendida(&z.riego);
      if (!quiereB && z.riego.encendido) z.riego.tFinPulso = ahora;
    } else if (z.enLinea) {
      quiereV = enVentana(z.vent, ahora);
      quiereB = gestionarRiego(z, ahora);
    } else {
      quiereV = false;
      quiereB = false;
      reiniciarRiego(z.riego);
    }
    escribirPin(z.vent.pin,  z.vent.encendido,  quiereV);
    escribirPin(z.riego.pin, z.riego.encendido, quiereB);
  }
}

int estadoZona(const Zona& z) { return z.manual ? 2 : (z.enLinea ? 1 : 0); }

int alarmas(const Zona& z) {
  if (!z.enLinea) return 0;
  return (z.riego.alarma ? 1 : 0) | (!valido(z.suelo) ? 2 : 0) | (!valido(z.temp) ? 4 : 0);
}

void armarLineaPantalla(char* out, size_t tam) {
  out[0] = '\0';
  char seg[110];
  for (int i = 0; i < NZ; i++) {
    const Zona& z = zonas[i];
    snprintf(seg, sizeof(seg), "%s%c,%.1f,%.0f,%.0f,%d,%d,%d,%.0f,%.1f,%.0f,%.0f,%.0f,%.0f,%d",
             i ? ";" : "", z.letra, z.temp, z.hr, z.suelo, estadoRiego(z), z.vent.encendido ? 1 : 0,
             estadoZona(z), z.vent.u, z.spTemp, z.sueloMin, z.sueloMax, z.hrMin, z.hrMax, alarmas(z));
    strncat(out, seg, tam - strlen(out) - 1);
  }
}

char macTexto[18]  = "??:??:??:??:??:??";
char macCodigo[80] = "";

void leerMiMAC() {
  uint8_t m[6] = {0};
  esp_wifi_get_mac(WIFI_IF_STA, m);
  snprintf(macTexto, sizeof(macTexto), "%02X:%02X:%02X:%02X:%02X:%02X", m[0], m[1], m[2], m[3], m[4], m[5]);
  snprintf(macCodigo, sizeof(macCodigo),
           "uint8_t MAC_MAESTRO[6] = {0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X};",
           m[0], m[1], m[2], m[3], m[4], m[5]);
}

void imprimirMAC() {
  Serial.println("==================================================");
  Serial.printf("MAESTRO  |  MAC: %s\n", macTexto);
  Serial.println("Copia esta linea en los 3 nodos (reemplaza la que tienen):");
  Serial.println(macCodigo);
  Serial.println("==================================================");
}

void imprimirMonitor() {
  static const char* txtRiego[3] = {"reposo ", "PULSO  ", "espera "};
  uint8_t ch = 0; wifi_second_chan_t ch2;
  esp_wifi_get_channel(&ch, &ch2);
  Serial.printf("[MAC %s | canal %d | ESP-NOW recibidos=%lu | WiFi %s | hora %s | Supabase ok=%lu fallos=%lu | ordenes web=%lu]\n",
                macTexto, ch, (unsigned long)rxTotal, wifiConectado ? "OK" : "--", horaOk ? "OK" : "--",
                (unsigned long)subidasOk, (unsigned long)subidasFallidas, (unsigned long)ordenesWeb);
  for (int i = 0; i < NZ; i++) {
    const Zona& z = zonas[i];
    Serial.printf("%-9s %s | T=%5.1f (obj %4.1f) uV=%5.1f%% I=%5.1f V:%s | suelo=%3.0f%% (banda %2.0f-%2.0f) riego:%s | HR=%3.0f%% (ideal %2.0f-%2.0f)%s | perdidos=%lu\n",
                  z.nombre, z.enLinea ? (z.manual ? "MAN " : "AUTO") : "OFF ",
                  z.temp, z.spTemp, z.vent.u, z.vent.I, z.vent.encendido ? "ON " : "off",
                  z.suelo, z.sueloMin, z.sueloMax, txtRiego[estadoRiego(z)],
                  z.hr, z.hrMin, z.hrMax, z.riego.alarma ? " | ALARMA RIEGO" : "",
                  (unsigned long)z.perdidos);
  }
  Serial.println("--------------------------------------------------------------------------");
}

int zonaPorLetra(char c) {
  for (int i = 0; i < NZ; i++) if (zonas[i].letra == c) return i;
  return -1;
}

bool ejecutarOrden(int i, const char* tipo, const char* valor, bool desdeWeb) {
  Zona& z = zonas[i];
  uint32_t ahora = millis();
  const char* fuente = desdeWeb ? "WEB" : "PANTALLA";

  if (strcmp(tipo, "MODO") == 0) {
    if (strcmp(valor, "MANUAL") == 0) {
      if (!z.manual) { z.manBomba = false; z.manVent = false; }
      z.manual = true; z.manualHasta = 0;
    } else pasarAAuto(z);
    Serial.printf("[%s] zona %s -> modo %s\n", fuente, z.nombre, z.manual ? "MANUAL" : "AUTO");
    return false;
  }
  if (strcmp(tipo, "VENT") == 0 || strcmp(tipo, "BOMBA") == 0) {
    if (!z.manual) {
      if (!desdeWeb) return false;
      z.manual = true; z.manBomba = false; z.manVent = false; z.manualHasta = 0;
    }
    z.manualHasta = desdeWeb ? ((ahora + MANUAL_WEB_MS) | 1) : 0;
    bool on = atoi(valor) != 0;
    if (tipo[0] == 'V') z.manVent = on;
    else { z.manBomba = on; if (on) z.manBombaDesde = ahora; }
    Serial.printf("[%s] zona %s -> %s %s\n", fuente, z.nombre, tipo[0] == 'V' ? "ventilador" : "bomba", on ? "ON" : "OFF");
    return false;
  }
  if (strcmp(tipo, "TOBJ") == 0) {
    z.spTemp = constrain((float)atof(valor), z.spMin, z.spMax);
    Serial.printf("[%s] zona %s -> T obj %.1f (rango %.0f-%.0f)\n", fuente, z.nombre, z.spTemp, z.spMin, z.spMax);
    return true;
  }
  return false;
}

int aplicarComando(char* l) {
  char* guarda;
  char* p0 = strtok_r(l, ",", &guarda);
  char* p1 = strtok_r(NULL, ",", &guarda);
  char* p2 = strtok_r(NULL, ",", &guarda);
  char* p3 = strtok_r(NULL, ",", &guarda);
  if (!p0 || !p1 || !p2 || !p3 || strcmp(p0, "CMD") != 0) return -1;
  int i = zonaPorLetra(p1[0]);
  if (i < 0) return -1;
  return ejecutarOrden(i, p2, p3, false) ? i : -1;
}

int leerComandosPantalla() {
  static char buf[64];
  static uint8_t n = 0;
  int guardar = -1;
  while (Serial2.available()) {
    char c = Serial2.read();
    if (c == '\n') {
      buf[n] = '\0';
      char copia[64]; strncpy(copia, buf, sizeof(copia));
      xSemaphoreTake(mutexZonas, portMAX_DELAY);
      int g = aplicarComando(copia);
      xSemaphoreGive(mutexZonas);
      if (g >= 0) guardar = g;
      n = 0;
    } else if (c != '\r') {
      if (n < sizeof(buf) - 1) buf[n++] = c; else n = 0;
    }
  }
  return guardar;
}

void tareaControl(void*) {
  uint32_t ultimoPID = 0, ultimaPantalla = 0;
  char linea[360];

  for (;;) {
    int g = leerComandosPantalla();
    if (g >= 0) guardarObjetivos(g);

    uint32_t ahora = millis();
    bool enviarPantalla = false;

    xSemaphoreTake(mutexZonas, portMAX_DELAY);
    tomarPaquetes(ahora);
    if (ahora - ultimoPID >= PERIODO_PID_MS) {
      ultimoPID = ahora;
      for (int i = 0; i < NZ; i++) calcularZona(zonas[i], ahora);
      imprimirMonitor();
    }
    actualizarReles(ahora);
    if (ahora - ultimaPantalla >= PERIODO_PANTALLA_MS) {
      ultimaPantalla = ahora;
      armarLineaPantalla(linea, sizeof(linea));
      enviarPantalla = true;
    }
    xSemaphoreGive(mutexZonas);

    if (enviarPantalla) Serial2.println(linea);
    vTaskDelay(pdMS_TO_TICKS(20));
  }
}

const bool usarWifi = strcmp(WIFI_SSID, "NOMBRE_DE_TU_RED") != 0;
const bool usarNube = usarWifi && strstr(SUPABASE_URL, "TU_PROYECTO") == NULL;

WiFiClientSecure tls;
HTTPClient       http;

int llamarRPC(const char* funcion, const char* cuerpo, bool objetoUnico, String* respuesta) {
  char url[200];
  snprintf(url, sizeof(url), "%s/rest/v1/rpc/%s", SUPABASE_URL, funcion);
  if (!http.begin(tls, url)) return -1;
  http.setTimeout(8000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("apikey", SUPABASE_KEY);
  if (strncmp(SUPABASE_KEY, "eyJ", 3) == 0)
    http.addHeader("Authorization", String("Bearer ") + SUPABASE_KEY);
  http.addHeader(CABECERA_CLAVE, CLAVE_DISPOSITIVO);
  if (objetoUnico) http.addHeader("Prefer", "params=single-object");
  int code = http.POST((uint8_t*)cuerpo, strlen(cuerpo));
  String r = (code > 0) ? http.getString() : String(http.errorToString(code));
  if (respuesta) *respuesta = r;
  if (code < 200 || code >= 300)
    Serial.printf("[NUBE] %s -> HTTP %d: %.200s\n", funcion, code, r.c_str());
  http.end();
  return code;
}

bool horaValida() { return time(nullptr) > 1700000000; }

void fechaISO(char* out, size_t tam) {
  struct timeval tv; gettimeofday(&tv, nullptr);
  struct tm t; gmtime_r(&tv.tv_sec, &t);
  snprintf(out, tam, "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ", t.tm_year + 1900, t.tm_mon + 1, t.tm_mday,
           t.tm_hour, t.tm_min, t.tm_sec, (int)(tv.tv_usec / 1000));
}

void uuid4(char* out) {
  uint8_t b[16];
  esp_fill_random(b, sizeof(b));
  b[6] = (b[6] & 0x0F) | 0x40;
  b[8] = (b[8] & 0x3F) | 0x80;
  sprintf(out, "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
          b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15]);
}

void subirLecturas() {
  Zona copia[NZ];
  xSemaphoreTake(mutexZonas, portMAX_DELAY);
  for (int i = 0; i < NZ; i++) copia[i] = zonas[i];
  xSemaphoreGive(mutexZonas);

  char fecha[32], id[40], cuerpo[768];
  for (int i = 0; i < NZ; i++) {
    const Zona& z = copia[i];
    if (!z.enLinea) continue;
    fechaISO(fecha, sizeof(fecha));
    uuid4(id);

    JsonDocument doc;
    JsonObject L = (ARG_LECTURA[0] == '\0') ? doc.to<JsonObject>() : doc[ARG_LECTURA].to<JsonObject>();
    L["id_mensaje"]  = id;
    L["dispositivo"] = DISPOSITIVO_ID;
    L["origen"]      = "real";
    L["zona"]        = z.nombre;
    L["medido_en"]   = fecha;
    bool ok = valido(z.temp) && valido(z.hr) && valido(z.suelo);
    L["calidad"]     = ok ? CALIDAD_BUENA : CALIDAD_MALA;
    JsonObject M = L["mediciones"].to<JsonObject>();
    if (valido(z.temp))  M["temperatura"]      = roundf(z.temp * 10) / 10;  else M["temperatura"]      = nullptr;
    if (valido(z.hr))    M["humedad_ambiente"] = roundf(z.hr * 10) / 10;    else M["humedad_ambiente"] = nullptr;
    if (valido(z.suelo)) M["humedad_sustrato"] = roundf(z.suelo * 10) / 10; else M["humedad_sustrato"] = nullptr;
    M["luz"] = nullptr; M["co2"] = nullptr; M["radiacion"] = nullptr;
    JsonObject A = L["actuadores"].to<JsonObject>();
    A["bomba"]      = z.riego.encendido ? "encendido" : "apagado";
    A["ventilador"] = z.vent.encendido  ? "encendido" : "apagado";
    A["luces"]      = "apagado";
    L["modo"] = z.manual ? "manual" : "automatico";
    serializeJson(doc, cuerpo, sizeof(cuerpo));

    int code = llamarRPC(FN_LECTURA, cuerpo, ARG_LECTURA[0] == '\0', nullptr);
    if (code >= 200 && code < 300) subidasOk = subidasOk + 1;
    else { subidasFallidas = subidasFallidas + 1; if (code < 0) return; }
  }
}

const char* texto(JsonVariantConst c, const char* a, const char* b, const char* d) {
  if (c[a].is<const char*>()) return c[a].as<const char*>();
  if (c[b].is<const char*>()) return c[b].as<const char*>();
  if (c[d].is<const char*>()) return c[d].as<const char*>();
  return "";
}
bool esEncendido(JsonVariantConst v) {
  if (v.is<bool>()) return v.as<bool>();
  if (v.is<int>())  return v.as<int>() != 0;
  const char* s = v | "";
  return !strcasecmp(s, "encendido") || !strcasecmp(s, "on") || !strcasecmp(s, "1") || !strcasecmp(s, "true");
}
int zonaPorNombre(const char* n) {
  for (int i = 0; i < NZ; i++) if (!strcasecmp(n, zonas[i].nombre)) return i;
  if (!strcasecmp(n, "templada")) return 1;
  if (!strcasecmp(n, "selva"))    return 2;
  return -1;
}

String hechos[8];
uint8_t idxHechos = 0;
bool yaHecho(const String& id) { for (auto& h : hechos) if (h == id) return true; return false; }

void confirmar(JsonVariantConst id) {
  JsonDocument d;
  d[ARG_CONF_ID] = id;
  if (ARG_CONF_RES[0]) d[ARG_CONF_RES] = VALOR_CONF_RES;
  char cuerpo[160];
  serializeJson(d, cuerpo, sizeof(cuerpo));
  llamarRPC(FN_CONFIRMAR, cuerpo, false, nullptr);
}

void revisarOrdenes() {
  char cuerpo[96] = "{}";
  if (ARG_PEND_DISP[0]) snprintf(cuerpo, sizeof(cuerpo), "{\"%s\":\"%s\"}", ARG_PEND_DISP, DISPOSITIVO_ID);
  String r;
  int code = llamarRPC(FN_PENDIENTES, cuerpo, false, &r);
  if (code != 200) return;

  JsonDocument doc;
  if (deserializeJson(doc, r)) return;
  JsonArrayConst lista = doc.as<JsonArrayConst>();
  for (JsonVariantConst c : lista) {
    String id = c["id"].as<String>();
    if (id.length() == 0 || id == "null") continue;
    if (yaHecho(id)) { confirmar(c["id"]); continue; }

    int i = zonaPorNombre(texto(c, "zona", "zona_id", "zona_nombre"));
    const char* act = texto(c, "actuador", "tipo", "comando");
    JsonVariantConst val = !c["accion"].isNull() ? c["accion"] : (!c["valor"].isNull() ? c["valor"] : c["estado"]);

    char tipo[8] = "", valor[16] = "";
    if (!strcasecmp(act, "ventilador") || !strcasecmp(act, "vent")) {
      strcpy(tipo, "VENT"); strcpy(valor, esEncendido(val) ? "1" : "0");
    } else if (!strcasecmp(act, "bomba") || !strcasecmp(act, "riego")) {
      strcpy(tipo, "BOMBA"); strcpy(valor, esEncendido(val) ? "1" : "0");
    } else if (!strcasecmp(act, "modo")) {
      const char* s = val | "";
      strcpy(tipo, "MODO"); strcpy(valor, !strcasecmp(s, "manual") ? "MANUAL" : "AUTO");
    } else if (strstr(act, "temp") || !strcasecmp(act, "setpoint")) {
      strcpy(tipo, "TOBJ"); snprintf(valor, sizeof(valor), "%.1f", val.as<float>());
    }

    if (i < 0 || !tipo[0]) {
      Serial.printf("[WEB] Orden no entendida: %s\n", c.as<String>().c_str());
    } else {
      xSemaphoreTake(mutexZonas, portMAX_DELAY);
      bool guardar = ejecutarOrden(i, tipo, valor, true);
      xSemaphoreGive(mutexZonas);
      if (guardar) guardarObjetivos(i);
      ordenesWeb = ordenesWeb + 1;
    }
    hechos[idxHechos] = id; idxHechos = (idxHechos + 1) % 8;
    confirmar(c["id"]);
  }
}

void tareaRed(void*) {
  uint32_t proximoIntentoWifi = 0, ultimaSubida = 0, ultimasOrdenes = 0;
  bool horaPedida = false;

  for (;;) {
    if (!usarWifi) { vTaskDelay(pdMS_TO_TICKS(1000)); continue; }
    uint32_t ahora = millis();

    if (WiFi.status() != WL_CONNECTED) {
      if (wifiConectado) { wifiConectado = false; proximoIntentoWifi = ahora; Serial.println("[RED] Se perdio el Wi-Fi"); }
      if ((int32_t)(ahora - proximoIntentoWifi) >= 0) {
        Serial.printf("[RED] Conectando a %s...\n", WIFI_SSID);
        WiFi.begin(WIFI_SSID, WIFI_PASS);
        uint32_t t0 = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - t0 < ESPERA_WIFI_MS) vTaskDelay(pdMS_TO_TICKS(200));
        if (WiFi.status() == WL_CONNECTED) {
          wifiConectado = true;
          Serial.printf("[RED] Wi-Fi OK. IP %s, canal %d (los nodos lo siguen)\n",
                        WiFi.localIP().toString().c_str(), (int)WiFi.channel());
          if (!horaPedida) { configTime(0, 0, "pool.ntp.org", "time.google.com"); horaPedida = true; }
        } else {
          WiFi.disconnect();
          fijarCanal(CANAL_RESPALDO);
          proximoIntentoWifi = millis() + REINTENTO_WIFI_MS;
          Serial.println("[RED] Sin Wi-Fi: modo local en canal 1 (el control sigue). Reintento en 2 min");
        }
      }
    } else {
      wifiConectado = true;
      horaOk = horaValida();
      if (usarNube) {
        if (horaOk && ahora - ultimaSubida >= PERIODO_SUBIDA_MS) { ultimaSubida = ahora; subirLecturas(); }
        if (ahora - ultimasOrdenes >= PERIODO_ORDENES_MS) { ultimasOrdenes = ahora; revisarOrdenes(); }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}

void setup() {
  const uint8_t PINES_RELE[6] = {33, 25, 26, 27, 14, 13};
  for (uint8_t p : PINES_RELE) { digitalWrite(p, RELE_OFF); pinMode(p, OUTPUT); }

  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);

  configurarZonas();
  prefs.begin("invernadero", false);
  cargarObjetivos();
  mutexZonas = xSemaphoreCreateMutex();

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, true);
  delay(100);
  WiFi.setSleep(false);
  WiFi.setAutoReconnect(false);
  fijarCanal(CANAL_RESPALDO);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error iniciando ESP-NOW. Reiniciando...");
    delay(2000);
    ESP.restart();
  }
  esp_now_register_recv_cb(alRecibir);

  tls.setInsecure();
  http.setReuse(true);

  leerMiMAC();
  imprimirMAC();
  if (!usarWifi)      Serial.println("[RED] Sin router configurado: ESP-NOW fijo en canal 1, sin nube");
  else if (!usarNube) Serial.println("[RED] Wi-Fi configurado pero falta SUPABASE_URL: sin nube");

  xTaskCreatePinnedToCore(tareaControl, "control", 8192,  NULL, 2, NULL, 1);
  xTaskCreatePinnedToCore(tareaRed,     "red",     16384, NULL, 1, NULL, 0);
}

void loop() {
  vTaskDelete(NULL);
}
