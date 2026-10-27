// ============================================================================
// BAJOTERRA - Prueba 01: conexión WiFi del ESP32 y hora UTC por internet (NTP).
// Objetivo: comprobar que la placa se conecta a la red, obtiene IP, tiene salida
// a internet y conoce la hora UTC (necesaria para fechar cada medición).
// Todavía NO envía datos al broker ni a la base de datos: eso es la Prueba 02.
// Funciona en una placa real y en el simulador Wokwi (red "Wokwi-GUEST").
// ============================================================================

// Biblioteca WiFi del ESP32 (viene con el paquete "esp32 by Espressif").
#include <WiFi.h>
// Funciones de fecha y hora de C (time, gmtime_r, strftime).
#include <time.h>

// Si existe secretos.h (copia de secretos.ejemplo.h con tus datos), se usa; ese archivo NO se sube a Git.
#if __has_include("secretos.h")
// Incluye el nombre y la clave de tu red WiFi.
#include "secretos.h"
// Si no existe, se usan los datos de la red simulada de Wokwi (abierta, sin clave).
#else
// Nombre de la red WiFi del simulador Wokwi.
#define WIFI_SSID "Wokwi-GUEST"
// La red de Wokwi no tiene clave.
#define WIFI_CLAVE ""
// Fin de la elección de credenciales.
#endif

// Pin del LED integrado de la placa (GPIO 2 en la mayoría de las ESP32 DevKit).
const int PIN_LED = 2;
// Tiempo máximo de espera para conectarse al WiFi al arrancar (20 segundos).
const unsigned long ESPERA_WIFI_MS = 20000;
// Cada cuánto se imprime el estado en el Monitor Serie (10 segundos).
const unsigned long INTERVALO_REPORTE_MS = 10000;
// Cada cuánto se reintenta la conexión si se pierde el WiFi (10 segundos).
const unsigned long INTERVALO_REINTENTO_MS = 10000;
// Servidores de hora (NTP) públicos.
const char* NTP_1 = "pool.ntp.org";
// Servidor de respaldo.
const char* NTP_2 = "time.google.com";

// Momento (en milisegundos desde el arranque) del último reporte impreso.
unsigned long ultimoReporte = 0;
// Momento del último intento de reconexión.
unsigned long ultimoReintento = 0;
// Indica si ya se obtuvo la hora real desde internet.
bool horaSincronizada = false;

// Convierte la intensidad de la señal (RSSI, en dBm) en una palabra fácil de entender.
const char* calidadSenal(int rssi) {
  // -55 dBm o más: señal muy buena.
  if (rssi >= -55) return "excelente";
  // Entre -67 y -55: buena.
  if (rssi >= -67) return "buena";
  // Entre -75 y -67: aceptable.
  if (rssi >= -75) return "regular";
  // Menos de -75: débil (puede cortarse).
  return "debil";
}

// Intenta conectarse al WiFi. Devuelve true si lo logra dentro del tiempo máximo.
bool conectarWifi() {
  // Modo estación: la placa se conecta a un router (no crea su propia red).
  WiFi.mode(WIFI_STA);
  // Si la conexión se cae, el ESP32 intenta volver a conectarse solo.
  WiFi.setAutoReconnect(true);
  // Inicia la conexión con el nombre y la clave de la red.
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
  // Avisa en el Monitor Serie a qué red se conecta (nunca se imprime la clave).
  Serial.printf("[wifi] conectando a \"%s\"", WIFI_SSID);
  // Guarda el momento de inicio para medir el tiempo de espera.
  unsigned long inicio = millis();
  // Espera mientras no esté conectado y no se haya agotado el tiempo.
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < ESPERA_WIFI_MS) {
    // Hace parpadear el LED para mostrar que está intentando.
    digitalWrite(PIN_LED, !digitalRead(PIN_LED));
    // Imprime un punto por cada intento.
    Serial.print('.');
    // Espera 250 ms antes de volver a revisar.
    delay(250);
  }
  // Salto de línea después de los puntos.
  Serial.println();
  // Si no se conectó, informa el código de estado y devuelve false.
  if (WiFi.status() != WL_CONNECTED) {
    // Apaga el LED: sin conexión.
    digitalWrite(PIN_LED, LOW);
    // Código numérico del estado (por ejemplo 1 = red no encontrada, 4 = falló la conexión).
    Serial.printf("[wifi] ERROR: no se pudo conectar (estado %d). Revisa nombre/clave y que la red sea de 2,4 GHz.\n", (int)WiFi.status());
    // No se conectó.
    return false;
  }
  // LED encendido fijo: conectado.
  digitalWrite(PIN_LED, HIGH);
  // Muestra la IP asignada, la señal y la dirección MAC de la placa.
  Serial.printf("[wifi] conectado. IP: %s | senal: %d dBm (%s) | MAC: %s\n",
                WiFi.localIP().toString().c_str(), (int)WiFi.RSSI(), calidadSenal(WiFi.RSSI()), WiFi.macAddress().c_str());
  // Conectado.
  return true;
}

// Pide la hora a internet (NTP) en UTC. Devuelve true si la obtuvo.
bool sincronizarHora() {
  // Configura la hora en UTC (desfase 0 y sin horario de verano) usando los dos servidores NTP.
  configTime(0, 0, NTP_1, NTP_2);
  // Estructura donde se guarda la fecha y hora separada en partes.
  struct tm partes;
  // Espera hasta 10 segundos a que llegue la hora.
  if (!getLocalTime(&partes, 10000)) {
    // No llegó: probablemente la red no tiene salida a internet.
    Serial.println("[hora] ERROR: no se obtuvo la hora por NTP (¿la red tiene salida a internet?).");
    // Sin hora.
    return false;
  }
  // Se obtuvo la hora.
  Serial.println("[hora] hora UTC sincronizada por NTP.");
  // Hora lista.
  return true;
}

// Escribe en "destino" la hora actual en formato ISO 8601 UTC, por ejemplo 2026-10-27T15:04:05Z.
void horaUtcIso(char* destino, size_t largo) {
  // Segundos desde 1970 según el reloj interno (ya sincronizado por NTP).
  time_t ahora = time(nullptr);
  // Partes de la fecha en UTC.
  struct tm partes;
  // Convierte a UTC de forma segura.
  gmtime_r(&ahora, &partes);
  // Da formato ISO 8601 con la "Z" final que indica UTC (igual que el contrato MQTT del proyecto).
  strftime(destino, largo, "%Y-%m-%dT%H:%M:%SZ", &partes);
}

// setup(): se ejecuta una sola vez al encender o reiniciar la placa.
void setup() {
  // Abre el Monitor Serie a 115200 baudios (configura lo mismo en el IDE).
  Serial.begin(115200);
  // Pequeña pausa para que el Monitor Serie alcance a abrirse.
  delay(300);
  // Configura el pin del LED como salida.
  pinMode(PIN_LED, OUTPUT);
  // Mensaje de inicio.
  Serial.println("\n=== BAJOTERRA - Prueba 01: WiFi + hora UTC ===");
  // Intenta conectarse al WiFi; si lo logra, pide la hora.
  if (conectarWifi()) {
    // Guarda si se pudo sincronizar la hora.
    horaSincronizada = sincronizarHora();
  }
}

// loop(): se repite sin parar mientras la placa esté encendida.
void loop() {
  // Momento actual en milisegundos desde el arranque.
  unsigned long ahora = millis();
  // Caso 1: se perdió la conexión WiFi.
  if (WiFi.status() != WL_CONNECTED) {
    // LED apagado mientras no hay red.
    digitalWrite(PIN_LED, LOW);
    // Reintenta cada INTERVALO_REINTENTO_MS (sin bloquear el programa).
    if (ahora - ultimoReintento >= INTERVALO_REINTENTO_MS) {
      // Recuerda cuándo fue este intento.
      ultimoReintento = ahora;
      // Avisa y pide reconectar.
      Serial.println("[wifi] conexion perdida, reintentando...");
      // Vuelve a conectar con los mismos datos.
      WiFi.reconnect();
    }
  // Caso 2: hay WiFi.
  } else {
    // LED encendido fijo.
    digitalWrite(PIN_LED, HIGH);
    // Si todavía no hay hora, la vuelve a pedir (por ejemplo, si la red no tenía internet al inicio).
    if (!horaSincronizada && ahora - ultimoReintento >= INTERVALO_REINTENTO_MS) {
      // Recuerda cuándo fue este intento.
      ultimoReintento = ahora;
      // Pide la hora otra vez.
      horaSincronizada = sincronizarHora();
    }
    // Cada INTERVALO_REPORTE_MS imprime el estado.
    if (ahora - ultimoReporte >= INTERVALO_REPORTE_MS) {
      // Recuerda cuándo fue este reporte.
      ultimoReporte = ahora;
      // Texto donde se escribe la hora.
      char hora[25];
      // Si hay hora real, la escribe; si no, lo dice (nunca inventa una fecha).
      if (horaSincronizada) horaUtcIso(hora, sizeof(hora));
      // Texto alternativo sin hora.
      else strcpy(hora, "sin-hora");
      // Imprime hora UTC, señal y memoria libre (útil para detectar fugas de memoria más adelante).
      Serial.printf("[estado] %s | senal %d dBm (%s) | memoria libre %lu bytes\n",
                    hora, (int)WiFi.RSSI(), calidadSenal(WiFi.RSSI()), (unsigned long)ESP.getFreeHeap());
    }
  }
  // Pequeña pausa para no ocupar la CPU al 100 %.
  delay(50);
}
