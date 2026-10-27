// ============================================================================
// BAJOTERRA - Prueba 02: el ESP32 envía lecturas a Supabase por HTTPS y recibe órdenes.
// (Opción A de docs/tiempo-real.md)
//
// Qué hace:
//  1. Se conecta al WiFi y obtiene la hora UTC (igual que la Prueba 01).
//  2. Cada 15 s envía una lectura con el formato del proyecto a la función registrar_lectura.
//     Como todavía no hay sensores, los valores son INVENTADOS y se envían con origen "simulado".
//  3. Cada 5 s pregunta si hay órdenes (comandos_pendientes). La orden "luces" enciende o apaga
//     el LED integrado (GPIO 2), que hace de "luces LED" en esta prueba. Otros actuadores se rechazan
//     porque aún no están conectados. Luego confirma el resultado (confirmar_comando).
//
// Requisitos:
//  - Paquete de placas "esp32 by Espressif" y la biblioteca "ArduinoJson" (versión 7) desde el Gestor de bibliotecas.
//  - Archivo secretos.h (copia de secretos.ejemplo.h) con el WiFi, la URL, la clave publicable y la clave del dispositivo.
//
// SEGURIDAD (limitación conocida de esta prueba): la conexión HTTPS va cifrada, pero NO se verifica el
// certificado del servidor (setInsecure). Se corregirá en una prueba posterior fijando el certificado raíz.
// ============================================================================

// WiFi del ESP32.
#include <WiFi.h>
// Cliente TLS (HTTPS).
#include <WiFiClientSecure.h>
// Cliente HTTP de alto nivel.
#include <HTTPClient.h>
// Creación y lectura de JSON (biblioteca ArduinoJson 7).
#include <ArduinoJson.h>
// Fecha y hora.
#include <time.h>
// Credenciales y datos del proyecto (este archivo NO se sube a Git).
#include "secretos.h"

// Pin del LED integrado: representa las "luces LED" de la zona en esta prueba.
const int PIN_LED = 2;
// Cada cuánto se envía una lectura (15 segundos).
const unsigned long INTERVALO_LECTURA_MS = 15000;
// Cada cuánto se preguntan las órdenes pendientes (5 segundos).
const unsigned long INTERVALO_ORDENES_MS = 5000;
// Tiempo máximo de espera de cada petición HTTPS (10 segundos).
const uint16_t ESPERA_HTTP_MS = 10000;

// Momento del último envío de lectura y de la última consulta de órdenes.
unsigned long ultimaLectura = 0;
unsigned long ultimasOrdenes = 0;
// Estado actual del LED ("luces").
bool lucesEncendidas = false;
// Últimos ids de órdenes procesadas (para no ejecutar dos veces la misma).
String idsProcesados[10];
// Posición donde se guardará el próximo id.
int posicionId = 0;

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------

// Genera un identificador UUID versión 4 (aleatorio) para cada mensaje, por ejemplo "3f2a...-4...-8...".
String nuevoUuid() {
  // 16 bytes aleatorios.
  uint8_t b[16];
  // Llena los bytes con el generador aleatorio por hardware del ESP32.
  for (int i = 0; i < 16; i += 4) {
    // Un número aleatorio de 32 bits.
    uint32_t r = esp_random();
    // Lo reparte en 4 bytes.
    memcpy(&b[i], &r, 4);
  }
  // Marca la versión 4 (bits 0100 en el byte 6).
  b[6] = (b[6] & 0x0F) | 0x40;
  // Marca la variante RFC 4122 (bits 10 en el byte 8).
  b[8] = (b[8] & 0x3F) | 0x80;
  // Texto resultante (36 caracteres + fin de cadena).
  char texto[37];
  // Formato 8-4-4-4-12 en hexadecimal.
  snprintf(texto, sizeof(texto), "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
           b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15]);
  // Devuelve el UUID.
  return String(texto);
}

// Devuelve la hora actual UTC en formato ISO 8601, por ejemplo "2026-10-27T15:04:05Z".
String horaUtcIso() {
  // Segundos desde 1970.
  time_t ahora = time(nullptr);
  // Partes de la fecha en UTC.
  struct tm partes;
  // Conversión segura a UTC.
  gmtime_r(&ahora, &partes);
  // Texto de salida.
  char texto[25];
  // Formato con "Z" (UTC).
  strftime(texto, sizeof(texto), "%Y-%m-%dT%H:%M:%SZ", &partes);
  // Devuelve el texto.
  return String(texto);
}

// Convierte una fecha ISO de Supabase ("2026-10-27T15:04:05.123+00:00") a segundos desde 1970 (UTC). 0 si no se entiende.
time_t isoASegundos(const char* iso) {
  // Partes de la fecha.
  struct tm partes = {};
  // Lee año, mes, día, hora, minuto y segundo (ignora fracciones y zona: Supabase responde en UTC).
  if (sscanf(iso, "%d-%d-%dT%d:%d:%d", &partes.tm_year, &partes.tm_mon, &partes.tm_mday,
             &partes.tm_hour, &partes.tm_min, &partes.tm_sec) != 6) return 0;
  // tm_year cuenta desde 1900.
  partes.tm_year -= 1900;
  // tm_mon va de 0 a 11.
  partes.tm_mon -= 1;
  // mktime usa la zona del sistema, que configTime(0, 0, ...) dejó en UTC.
  return mktime(&partes);
}

// Indica si un id de orden ya se procesó.
bool yaProcesado(const String& id) {
  // Recorre los ids guardados.
  for (int i = 0; i < 10; i++) {
    // Si coincide, ya se procesó.
    if (idsProcesados[i] == id) return true;
  }
  // No estaba.
  return false;
}

// Guarda un id procesado (reemplaza el más antiguo cuando la lista está llena).
void recordarId(const String& id) {
  // Guarda en la posición actual.
  idsProcesados[posicionId] = id;
  // Avanza en círculo (0..9).
  posicionId = (posicionId + 1) % 10;
}

// ---------------------------------------------------------------------------
// Comunicación con Supabase
// ---------------------------------------------------------------------------

// Llama a una función de la base de datos (RPC). Devuelve true si respondió bien; deja la respuesta en "respuesta".
bool llamarRpc(const char* funcion, JsonDocument& cuerpo, JsonDocument& respuesta) {
  // Cliente TLS (HTTPS).
  WiFiClientSecure tls;
  // LIMITACIÓN DE LA PRUEBA: no verifica el certificado del servidor (ver encabezado).
  tls.setInsecure();
  // Cliente HTTP.
  HTTPClient http;
  // Tiempo máximo de espera.
  http.setTimeout(ESPERA_HTTP_MS);
  // Dirección completa: https://<proyecto>.supabase.co/rest/v1/rpc/<funcion>
  String url = String(SUPABASE_URL) + "/rest/v1/rpc/" + funcion;
  // Abre la conexión.
  if (!http.begin(tls, url)) {
    // No se pudo preparar la conexión.
    Serial.println("[http] ERROR: no se pudo iniciar la conexion");
    return false;
  }
  // La clave publicable va en el encabezado "apikey" (no en Authorization).
  http.addHeader("apikey", SUPABASE_PUBLISHABLE_KEY);
  // El cuerpo es JSON.
  http.addHeader("Content-Type", "application/json");
  // Convierte el cuerpo a texto.
  String texto;
  serializeJson(cuerpo, texto);
  // Envía la petición POST.
  int codigo = http.POST(texto);
  // Lee la respuesta como texto.
  String recibido = http.getString();
  // Cierra la conexión y libera memoria.
  http.end();
  // Códigos 200-299 = éxito.
  if (codigo < 200 || codigo >= 300) {
    // Muestra el código y el mensaje de Supabase (por ejemplo "clave de dispositivo inválida").
    Serial.printf("[http] %s respondio %d: %s\n", funcion, codigo, recibido.c_str());
    return false;
  }
  // Respuesta vacía: no hay nada que leer.
  if (recibido.length() == 0) return true;
  // Convierte el texto JSON en datos.
  DeserializationError fallo = deserializeJson(respuesta, recibido);
  // Si el JSON no es válido, lo informa.
  if (fallo) {
    Serial.printf("[json] respuesta ilegible de %s: %s\n", funcion, fallo.c_str());
    return false;
  }
  // Todo bien.
  return true;
}

// Arma y envía una lectura. Los valores son INVENTADOS (no hay sensores todavía): por eso origen = "simulado".
void enviarLectura() {
  // Documento JSON del cuerpo.
  JsonDocument cuerpo;
  // Clave propia del dispositivo.
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  // Objeto con la lectura (mismo formato de docs/mqtt-topics.md).
  JsonObject lectura = cuerpo["p_lectura"].to<JsonObject>();
  // Identificador único del mensaje.
  lectura["id_mensaje"] = nuevoUuid();
  // Nombre del dispositivo (debe coincidir con el registrado en Supabase).
  lectura["dispositivo"] = DISPOSITIVO_ID;
  // Datos inventados: se declaran SIMULADOS.
  lectura["origen"] = "simulado";
  // Hora de la medición en UTC.
  lectura["medido_en"] = horaUtcIso();
  // Calidad declarada.
  lectura["calidad"] = "buena";
  // Mediciones inventadas con una pequeña variación aleatoria.
  JsonObject m = lectura["mediciones"].to<JsonObject>();
  // Temperatura entre 26 y 28 °C.
  m["temperatura"] = 26.0 + (esp_random() % 200) / 100.0;
  // Humedad del aire entre 88 y 92 %.
  m["humedad_ambiente"] = 88.0 + (esp_random() % 400) / 100.0;
  // Humedad del sustrato entre 60 y 65 %.
  m["humedad_sustrato"] = 60.0 + (esp_random() % 500) / 100.0;
  // Luz: más alta si el LED está encendido (imita el aporte de las luces LED).
  m["luz"] = (lucesEncendidas ? 5200 : 3700) + (int)(esp_random() % 300);
  // CO2 entre 700 y 850 ppm.
  m["co2"] = 700 + (int)(esp_random() % 150);
  // Sin sensor de radiación: null (nunca 0).
  m["radiacion"] = nullptr;
  // Estado de los actuadores: solo las "luces" existen en esta prueba; los demás no se informan (null).
  JsonObject a = lectura["actuadores"].to<JsonObject>();
  // Estado real del LED.
  a["luces"] = lucesEncendidas ? "encendido" : "apagado";
  // Bomba y extractor no conectados: sin dato.
  a["bomba"] = nullptr;
  a["ventilador"] = nullptr;
  // Documento para la respuesta.
  JsonDocument respuesta;
  // Envía y muestra el resultado ("guardado" o "duplicado").
  if (llamarRpc("registrar_lectura", cuerpo, respuesta)) {
    Serial.printf("[lectura] %s %s\n", horaUtcIso().c_str(), respuesta["estado"] | "?");
  }
}

// Envía la confirmación de una orden.
void confirmarOrden(const char* id, const char* resultado, const char* detalle) {
  // Cuerpo de la petición.
  JsonDocument cuerpo;
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  cuerpo["p_id_comando"] = id;
  cuerpo["p_resultado"] = resultado;
  // "simulado": en esta prueba el LED solo representa a las luces reales.
  cuerpo["p_origen"] = "simulado";
  cuerpo["p_detalle"] = detalle;
  // Respuesta.
  JsonDocument respuesta;
  // Envía.
  if (llamarRpc("confirmar_comando", cuerpo, respuesta)) {
    Serial.printf("[orden] confirmada %s -> %s\n", id, resultado);
  }
}

// Pregunta las órdenes pendientes y las ejecuta.
void atenderOrdenes() {
  // Cuerpo: solo la clave del dispositivo.
  JsonDocument cuerpo;
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  // Respuesta: una lista de órdenes.
  JsonDocument respuesta;
  // Si falla, se reintenta en el siguiente ciclo.
  if (!llamarRpc("comandos_pendientes", cuerpo, respuesta)) return;
  // Recorre cada orden.
  for (JsonObject orden : respuesta.as<JsonArray>()) {
    // Datos de la orden.
    const char* id = orden["id_comando"] | "";
    const char* actuador = orden["actuador"] | "";
    const char* estado = orden["estado_solicitado"] | "";
    const char* caduca = orden["caduca_en"] | "";
    // Muestra la orden recibida.
    Serial.printf("[orden] recibida %s: %s -> %s\n", id, actuador, estado);
    // Si ya se procesó (llegó repetida), se informa "duplicado" sin repetir la acción.
    if (yaProcesado(String(id))) {
      confirmarOrden(id, "duplicado", "orden ya procesada");
      continue;
    }
    // Recuerda el id.
    recordarId(String(id));
    // Si ya venció, NO se ejecuta (regla de seguridad).
    time_t limite = isoASegundos(caduca);
    if (limite == 0 || time(nullptr) > limite) {
      confirmarOrden(id, "caducado", "la orden llego vencida");
      continue;
    }
    // Las "luces" son el LED integrado.
    if (strcmp(actuador, "luces") == 0) {
      // Encender o apagar según lo pedido.
      lucesEncendidas = strcmp(estado, "encendido") == 0;
      // Aplica al LED.
      digitalWrite(PIN_LED, lucesEncendidas ? HIGH : LOW);
      // Confirma la ejecución.
      confirmarOrden(id, "ejecutado", lucesEncendidas ? "LED integrado encendido (prueba 02)" : "LED integrado apagado (prueba 02)");
    } else {
      // Bomba y extractor aún no están conectados.
      confirmarOrden(id, "rechazado", "actuador no conectado en la prueba 02");
    }
  }
}

// ---------------------------------------------------------------------------
// WiFi y hora (igual que la Prueba 01, en versión corta)
// ---------------------------------------------------------------------------

// Conecta al WiFi; espera hasta 20 s.
bool conectarWifi() {
  // Modo estación con reconexión automática.
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  // Inicia la conexión.
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
  Serial.printf("[wifi] conectando a \"%s\"", WIFI_SSID);
  // Espera.
  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 20000) {
    Serial.print('.');
    delay(250);
  }
  Serial.println();
  // Resultado.
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[wifi] ERROR: sin conexion (revisa nombre/clave y que sea 2,4 GHz)");
    return false;
  }
  Serial.printf("[wifi] conectado. IP: %s | senal: %d dBm\n", WiFi.localIP().toString().c_str(), (int)WiFi.RSSI());
  return true;
}

// Sincroniza la hora UTC por NTP; espera hasta 10 s.
bool sincronizarHora() {
  // UTC, sin horario de verano.
  configTime(0, 0, "pool.ntp.org", "time.google.com");
  // Espera a tener la hora.
  struct tm partes;
  if (!getLocalTime(&partes, 10000)) {
    Serial.println("[hora] ERROR: sin hora NTP");
    return false;
  }
  Serial.println("[hora] hora UTC sincronizada");
  return true;
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

// setup(): una vez al encender.
void setup() {
  // Monitor Serie a 115200 baudios.
  Serial.begin(115200);
  delay(300);
  // LED apagado al inicio.
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  Serial.println("\n=== BAJOTERRA - Prueba 02: lecturas y ordenes con Supabase ===");
  Serial.printf("[config] dispositivo: %s\n", DISPOSITIVO_ID);
  // WiFi y hora: sin hora no se envían lecturas (Supabase rechaza fechas inválidas).
  while (!conectarWifi()) delay(5000);
  while (!sincronizarHora()) delay(5000);
}

// loop(): se repite sin parar.
void loop() {
  // Sin WiFi no se intenta nada (la reconexión es automática).
  if (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    return;
  }
  // Momento actual.
  unsigned long ahora = millis();
  // ¿Toca enviar una lectura? (la primera sale de inmediato)
  if (ultimaLectura == 0 || ahora - ultimaLectura >= INTERVALO_LECTURA_MS) {
    ultimaLectura = ahora;
    enviarLectura();
  }
  // ¿Toca preguntar por órdenes?
  if (ahora - ultimasOrdenes >= INTERVALO_ORDENES_MS) {
    ultimasOrdenes = ahora;
    atenderOrdenes();
  }
  // Pausa corta para no ocupar la CPU al 100 %.
  delay(50);
}
