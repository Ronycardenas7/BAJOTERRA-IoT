// ============================================================================
// BAJOTERRA - Controlador v1 (ESP32 DevKit): 3 zonas con cable, control local y nube.
//
// Qué hace:
//  1. Cada 3 s lee los DHT22 (temperatura y humedad del aire) y las sondas de suelo de las 3 zonas.
//  2. Decide SOLO (aunque no haya internet): riego con histéresis y ventilación por temperatura/humedad.
//     Seguridad: una bomba nunca pasa de 20 s seguidos y luego descansa 30 s. Sin dato de suelo NO riega.
//  3. Cada 2 s envía una línea JSON por UART (GPIO 17) para la pantalla CYD.
//  4. Cada 15 s envía una lectura por zona a Supabase (registrar_lectura) con un solo dispositivo "controlador".
//  5. Cada 5 s pregunta órdenes de la web (comandos_pendientes), las ejecuta en modo manual por 2 min y confirma.
//
// Datos: con MODO_WOKWI = 1 todo se declara origen "simulado"; con la placa física, "real".
// Un sensor que no existe o falla se envía como null (nunca 0).
//
// Bibliotecas: "DHT sensor library" + "Adafruit Unified Sensor" (Adafruit) y "ArduinoJson" (v7).
// Placa: "ESP32 Dev Module".
//
// SEGURIDAD (limitación conocida): HTTPS cifrado pero sin verificar el certificado (setInsecure), igual que la prueba 02.
// ============================================================================

// Credenciales (y, en Wokwi, MODO_WOKWI). Va PRIMERO para que config.h vea MODO_WOKWI.
#include "secretos.h"
// Pines, zonas y umbrales.
#include "config.h"
// WiFi del ESP32.
#include <WiFi.h>
// Cliente TLS (HTTPS).
#include <WiFiClientSecure.h>
// Cliente HTTP.
#include <HTTPClient.h>
// JSON (ArduinoJson 7).
#include <ArduinoJson.h>
// Sensor DHT22 (biblioteca de Adafruit).
#include <DHT.h>
// Fecha y hora.
#include <time.h>

// Texto del origen de los datos según el modo.
const char* const ORIGEN = MODO_WOKWI ? "simulado" : "real";

// ---------------------------------------------------------------------------
// Estado de cada zona (cambia mientras el programa corre)
// ---------------------------------------------------------------------------

// Lo que se sabe de una zona en este momento.
struct EstadoZona {
  // Temperatura del aire en °C (NAN = sin dato).
  float temperatura = NAN;
  // Humedad del aire en % (NAN = sin dato).
  float humedadAire = NAN;
  // Humedad del suelo en % (NAN = sin dato).
  float humedadSuelo = NAN;
  // Último valor crudo del ADC de la sonda (para depurar la calibración).
  int crudoSuelo = -1;
  // Hasta cuándo (millis) la bomba está en modo manual; 0 = automático.
  unsigned long bombaManualHasta = 0;
  // Hasta cuándo el ventilador está en modo manual; 0 = automático.
  unsigned long ventiladorManualHasta = 0;
};

// Estado de las 3 zonas.
EstadoZona estado[NUM_ZONAS];
// Sensores DHT creados al iniciar (nullptr si la zona no tiene DHT22).
DHT* sensoresDht[NUM_ZONAS] = {nullptr, nullptr, nullptr};

// Estado lógico de cada relé (true = encendido).
bool releEncendido[4] = {false, false, false, false};
// Momento en que se encendió cada relé (para el límite de las bombas).
unsigned long releEncendidoDesde[4] = {0, 0, 0, 0};
// Hasta cuándo cada relé de bomba debe descansar (no puede encenderse).
unsigned long releDescansoHasta[4] = {0, 0, 0, 0};
// true si el relé es de una bomba (se calcula al iniciar desde la tabla de zonas).
bool releEsBomba[4] = {false, false, false, false};

// Momentos de la última vez que se hizo cada tarea.
unsigned long ultimoSensores = 0;
unsigned long ultimaPantalla = 0;
unsigned long ultimaNube = 0;
unsigned long ultimasOrdenes = 0;
// Último intento de sincronizar la hora.
unsigned long ultimoIntentoHora = 0;

// Últimos ids de órdenes procesadas (evita ejecutar dos veces la misma).
String idsProcesados[10];
// Posición donde se guarda el próximo id.
int posicionId = 0;

// Conexión TLS y cliente HTTP globales: se reutilizan para no negociar TLS en cada petición.
WiFiClientSecure tls;
// Cliente HTTP.
HTTPClient http;

// ---------------------------------------------------------------------------
// Relés
// ---------------------------------------------------------------------------

// Escribe el nivel eléctrico de un relé según su estado lógico y la polaridad del módulo.
void aplicarRele(int indice) {
  // Encendido + activo en LOW = LOW; encendido + activo en HIGH = HIGH (y al revés para apagado).
  bool nivelAlto = releEncendido[indice] != RELE_ACTIVO_BAJO;
  // Escribe el pin.
  digitalWrite(PINES_RELE[indice], nivelAlto ? HIGH : LOW);
}

// Cambia un relé respetando la seguridad de las bombas. Devuelve false si no se pudo encender.
bool cambiarRele(int indice, bool encender, const char* motivo) {
  // Índice fuera de rango: no hace nada.
  if (indice < 0 || indice > 3) return false;
  // Sin cambio: nada que hacer.
  if (releEncendido[indice] == encender) return true;
  // Momento actual.
  unsigned long ahora = millis();
  // Una bomba en descanso no puede encenderse.
  if (encender && releEsBomba[indice] && (long)(releDescansoHasta[indice] - ahora) > 0) return false;
  // Guarda el nuevo estado.
  releEncendido[indice] = encender;
  // Si se enciende, anota cuándo.
  if (encender) releEncendidoDesde[indice] = ahora;
  // Si se apaga una bomba, empieza su descanso.
  if (!encender && releEsBomba[indice]) releDescansoHasta[indice] = ahora + BOMBA_DESCANSO_MS;
  // Aplica al pin.
  aplicarRele(indice);
  // Lo informa en el Monitor Serie.
  Serial.printf("[rele] %s -> %s (%s)\n", NOMBRES_RELE[indice], encender ? "ENCENDIDO" : "apagado", motivo);
  // Cambio hecho.
  return true;
}

// Seguridad de las bombas: apaga cualquier bomba que lleve más de BOMBA_MAX_MS encendida.
// Se llama en cada vuelta del loop y antes de cada petición HTTPS (que puede tardar varios segundos).
void vigilarBombas() {
  // Momento actual.
  unsigned long ahora = millis();
  // Revisa los 4 relés.
  for (int i = 0; i < 4; i++) {
    // Solo bombas encendidas que superaron el límite.
    if (releEsBomba[i] && releEncendido[i] && ahora - releEncendidoDesde[i] >= BOMBA_MAX_MS) {
      // Apaga por seguridad (también corta el modo manual de esa bomba).
      cambiarRele(i, false, "limite de tiempo de seguridad");
    }
  }
}

// ---------------------------------------------------------------------------
// Sensores
// ---------------------------------------------------------------------------

// Convierte el valor crudo de la sonda a % de humedad. NAN si la calibración es inválida.
float sueloAPorcentaje(int crudo, int seco, int mojado) {
  // Calibración imposible (seco y mojado iguales): sin dato.
  if (seco == mojado) return NAN;
  // Regla de tres: seco = 0 %, mojado = 100 %.
  float porcentaje = (float)(seco - crudo) * 100.0f / (float)(seco - mojado);
  // Limita a 0..100 %.
  return constrain(porcentaje, 0.0f, 100.0f);
}

// Lee los DHT22 y las sondas de suelo de las 3 zonas.
void leerSensores() {
  // Enciende la alimentación de las sondas de suelo.
  digitalWrite(PIN_ALIM_SUELO, HIGH);
  // Espera a que la señal se estabilice.
  delay(50);
  // Recorre las zonas.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Configuración de la zona.
    const ConfigZona& c = ZONAS[z];
    // --- Suelo ---
    if (c.pinSuelo >= 0) {
      // Suma de 16 muestras para reducir el ruido.
      long suma = 0;
      // Toma las muestras.
      for (int i = 0; i < 16; i++) suma += analogRead(c.pinSuelo);
      // Promedio.
      int crudo = suma / 16;
      // Lo guarda para depurar.
      estado[z].crudoSuelo = crudo;
      // Valores pegados al extremo (< 50 o > 4080) indican sonda desconectada o en corto: sin dato (no se riega).
      if (crudo < 50 || crudo > 4080) {
        // Sin dato.
        estado[z].humedadSuelo = NAN;
      } else {
        // Convierte a %.
        estado[z].humedadSuelo = sueloAPorcentaje(crudo, c.crudoSeco, c.crudoMojado);
      }
    }
    // --- Aire (DHT22) ---
    if (sensoresDht[z] != nullptr) {
      // Temperatura en °C (NAN si el sensor no responde).
      estado[z].temperatura = sensoresDht[z]->readTemperature();
      // Humedad relativa en % (NAN si no responde).
      estado[z].humedadAire = sensoresDht[z]->readHumidity();
    }
  }
  // Apaga la alimentación de las sondas (evita la corrosión).
  digitalWrite(PIN_ALIM_SUELO, LOW);
}

// ---------------------------------------------------------------------------
// Control automático
// ---------------------------------------------------------------------------

// Indica si un momento "hasta" (millis) todavía no llega.
bool vigente(unsigned long hasta) {
  // 0 = no hay modo manual; si no, compara con el reloj (resistente al desborde de millis).
  return hasta != 0 && (long)(hasta - millis()) > 0;
}

// Decide bomba y ventilador de cada zona que esté en automático.
void controlar() {
  // Recorre las zonas.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Configuración y estado de la zona.
    const ConfigZona& c = ZONAS[z];
    EstadoZona& e = estado[z];
    // --- Riego ---
    if (c.releBomba >= 0 && !vigente(e.bombaManualHasta)) {
      // Si el modo manual terminó, se borra.
      e.bombaManualHasta = 0;
      // Sin dato de suelo: la bomba se apaga (nunca se riega a ciegas).
      if (isnan(e.humedadSuelo)) {
        cambiarRele(c.releBomba, false, "sin dato de suelo");
      } else if (e.humedadSuelo < c.sueloEncender) {
        // Suelo seco: intenta regar (si la bomba está descansando, esperará).
        cambiarRele(c.releBomba, true, "suelo seco (automatico)");
      } else if (e.humedadSuelo >= c.sueloApagar) {
        // Suelo suficientemente húmedo: deja de regar.
        cambiarRele(c.releBomba, false, "suelo humedo (automatico)");
      }
      // Entre ambos umbrales se mantiene como está (histéresis).
    }
    // --- Ventilación ---
    if (c.releVentilador >= 0 && !vigente(e.ventiladorManualHasta)) {
      // Si el modo manual terminó, se borra.
      e.ventiladorManualHasta = 0;
      // ¿Hace demasiado calor o hay demasiada humedad? (NAN compara siempre como falso)
      bool exceso = e.temperatura > c.temperaturaMax || e.humedadAire > c.humedadAireMax;
      // ¿Ya bajó lo suficiente las dos variables? (sin dato cuenta como "bajó": el ventilador no queda prendido sin razón)
      bool normal = !(e.temperatura >= c.temperaturaMax - HISTERESIS_TEMPERATURA)
                    && !(e.humedadAire >= c.humedadAireMax - HISTERESIS_HUMEDAD);
      // Enciende con exceso.
      if (exceso) cambiarRele(c.releVentilador, true, "calor o humedad alta (automatico)");
      // Apaga cuando todo volvió a la normalidad.
      else if (normal) cambiarRele(c.releVentilador, false, "condiciones normales (automatico)");
    }
  }
}

// ---------------------------------------------------------------------------
// Utilidades de texto, hora e ids
// ---------------------------------------------------------------------------

// Genera un UUID versión 4 aleatorio para cada mensaje.
String nuevoUuid() {
  // 16 bytes aleatorios.
  uint8_t b[16];
  // Llena los bytes con el generador por hardware del ESP32.
  for (int i = 0; i < 16; i += 4) {
    // Número aleatorio de 32 bits.
    uint32_t r = esp_random();
    // Lo reparte en 4 bytes.
    memcpy(&b[i], &r, 4);
  }
  // Versión 4.
  b[6] = (b[6] & 0x0F) | 0x40;
  // Variante RFC 4122.
  b[8] = (b[8] & 0x3F) | 0x80;
  // Texto de salida.
  char texto[37];
  // Formato 8-4-4-4-12.
  snprintf(texto, sizeof(texto), "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",
           b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15]);
  // Devuelve el UUID.
  return String(texto);
}

// true cuando el reloj ya tiene la hora real (posterior a 2023).
bool horaValida() {
  // 1700000000 s = noviembre de 2023.
  return time(nullptr) > 1700000000;
}

// Hora actual UTC en ISO 8601, por ejemplo "2026-10-27T15:04:05Z".
String horaUtcIso() {
  // Segundos desde 1970.
  time_t ahora = time(nullptr);
  // Partes de la fecha en UTC.
  struct tm partes;
  // Conversión a UTC.
  gmtime_r(&ahora, &partes);
  // Texto de salida.
  char texto[25];
  // Formato con "Z".
  strftime(texto, sizeof(texto), "%Y-%m-%dT%H:%M:%SZ", &partes);
  // Devuelve el texto.
  return String(texto);
}

// Convierte una fecha ISO de Supabase a segundos desde 1970 (UTC). 0 si no se entiende.
time_t isoASegundos(const char* iso) {
  // Partes de la fecha.
  struct tm partes = {};
  // Lee año, mes, día, hora, minuto y segundo.
  if (sscanf(iso, "%d-%d-%dT%d:%d:%d", &partes.tm_year, &partes.tm_mon, &partes.tm_mday,
             &partes.tm_hour, &partes.tm_min, &partes.tm_sec) != 6) return 0;
  // tm_year cuenta desde 1900.
  partes.tm_year -= 1900;
  // tm_mon va de 0 a 11.
  partes.tm_mon -= 1;
  // configTime(0, 0, ...) dejó la zona en UTC, así que mktime trabaja en UTC.
  return mktime(&partes);
}

// Indica si un id de orden ya se procesó.
bool yaProcesado(const String& id) {
  // Recorre los ids guardados.
  for (int i = 0; i < 10; i++) {
    // Coincide: ya se procesó.
    if (idsProcesados[i] == id) return true;
  }
  // No estaba.
  return false;
}

// Guarda un id procesado (reemplaza el más antiguo).
void recordarId(const String& id) {
  // Guarda en la posición actual.
  idsProcesados[posicionId] = id;
  // Avanza en círculo.
  posicionId = (posicionId + 1) % 10;
}

// Escribe un número en JSON, o null si no hay dato (NAN).
void ponerNumero(JsonObject obj, const char* clave, float valor, int decimales) {
  // Sin dato: null (nunca 0).
  if (isnan(valor)) {
    obj[clave] = nullptr;
  } else {
    // Redondea a los decimales pedidos.
    float factor = pow(10, decimales);
    // Guarda el valor redondeado.
    obj[clave] = roundf(valor * factor) / factor;
  }
}

// Estado de un actuador para el JSON: "encendido", "apagado" o null si la zona no lo tiene.
void ponerActuador(JsonObject obj, const char* clave, int indiceRele) {
  // La zona no tiene ese actuador: null.
  if (indiceRele < 0) obj[clave] = nullptr;
  // Estado real del relé.
  else obj[clave] = releEncendido[indiceRele] ? "encendido" : "apagado";
}

// ---------------------------------------------------------------------------
// Pantalla CYD (UART de un solo sentido)
// ---------------------------------------------------------------------------

// Envía una línea JSON con las 3 zonas, por ejemplo {"wifi":true,"zonas":[{"n":"arida","t":31.2,...}]}.
void enviarPantalla() {
  // Documento JSON.
  JsonDocument doc;
  // ¿Hay WiFi?
  doc["wifi"] = WiFi.status() == WL_CONNECTED;
  // Origen de los datos (la pantalla debe mostrar "SIMULADO" si corresponde).
  doc["origen"] = ORIGEN;
  // Hora UTC si está disponible; si no, null.
  if (horaValida()) doc["hora"] = horaUtcIso(); else doc["hora"] = nullptr;
  // Lista de zonas.
  JsonArray lista = doc["zonas"].to<JsonArray>();
  // Recorre las zonas.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Objeto de la zona.
    JsonObject o = lista.add<JsonObject>();
    // Nombre.
    o["n"] = ZONAS[z].nombre;
    // Temperatura, humedad del aire y del suelo (null sin dato).
    ponerNumero(o, "t", estado[z].temperatura, 1);
    ponerNumero(o, "ha", estado[z].humedadAire, 0);
    ponerNumero(o, "hs", estado[z].humedadSuelo, 0);
    // Bomba y ventilador.
    ponerActuador(o, "b", ZONAS[z].releBomba);
    ponerActuador(o, "v", ZONAS[z].releVentilador);
    // ¿Algún actuador en manual?
    o["m"] = vigente(estado[z].bombaManualHasta) || vigente(estado[z].ventiladorManualHasta);
  }
  // Escribe la línea por el UART y termina con salto de línea.
  serializeJson(doc, Serial2);
  // Fin de la línea.
  Serial2.println();
}

// ---------------------------------------------------------------------------
// Supabase
// ---------------------------------------------------------------------------

// Llama a una función RPC de Supabase. true si respondió bien; la respuesta queda en "respuesta".
bool llamarRpc(const char* funcion, JsonDocument& cuerpo, JsonDocument& respuesta) {
  // La petición puede tardar: antes revisa la seguridad de las bombas.
  vigilarBombas();
  // Dirección: https://<proyecto>.supabase.co/rest/v1/rpc/<funcion>
  String url = String(SUPABASE_URL) + "/rest/v1/rpc/" + funcion;
  // Prepara la petición (reutiliza la conexión TLS si sigue abierta).
  if (!http.begin(tls, url)) {
    // No se pudo preparar.
    Serial.println("[http] ERROR: no se pudo iniciar la conexion");
    return false;
  }
  // Clave publicable en el encabezado "apikey".
  http.addHeader("apikey", SUPABASE_PUBLISHABLE_KEY);
  // Cuerpo JSON.
  http.addHeader("Content-Type", "application/json");
  // Convierte el cuerpo a texto.
  String texto;
  // Serializa.
  serializeJson(cuerpo, texto);
  // Envía por POST.
  int codigo = http.POST(texto);
  // Lee la respuesta.
  String recibido = http.getString();
  // Termina la petición (con setReuse la conexión queda abierta para la próxima).
  http.end();
  // Después de esperar la red, vuelve a revisar las bombas.
  vigilarBombas();
  // Error HTTP o de red (código negativo).
  if (codigo < 200 || codigo >= 300) {
    // Muestra el código y el mensaje (por ejemplo "clave de dispositivo inválida").
    Serial.printf("[http] %s respondio %d: %s\n", funcion, codigo, recibido.c_str());
    return false;
  }
  // Respuesta vacía: listo.
  if (recibido.length() == 0) return true;
  // Interpreta el JSON.
  DeserializationError fallo = deserializeJson(respuesta, recibido);
  // JSON inválido.
  if (fallo) {
    // Lo informa.
    Serial.printf("[json] respuesta ilegible de %s: %s\n", funcion, fallo.c_str());
    return false;
  }
  // Todo bien.
  return true;
}

// Envía la lectura de una zona.
void enviarLecturaZona(int z) {
  // Configuración y estado.
  const ConfigZona& c = ZONAS[z];
  // Estado actual.
  const EstadoZona& e = estado[z];
  // Cuerpo de la petición.
  JsonDocument cuerpo;
  // Clave del controlador.
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  // Lectura con el formato de docs/mqtt-topics.md.
  JsonObject lectura = cuerpo["p_lectura"].to<JsonObject>();
  // Id único del mensaje.
  lectura["id_mensaje"] = nuevoUuid();
  // Nombre del dispositivo (debe coincidir con la clave).
  lectura["dispositivo"] = DISPOSITIVO_ID;
  // Zona a la que pertenece la lectura (obligatorio para un controlador).
  lectura["zona"] = c.nombre;
  // Real o simulado según el modo.
  lectura["origen"] = ORIGEN;
  // Hora UTC.
  lectura["medido_en"] = horaUtcIso();
  // Cuenta cuántos sensores existentes fallaron.
  int fallas = 0;
  // Cuántos sensores tiene la zona.
  int sensores = 0;
  // DHT22 existente: cuenta y revisa.
  if (c.pinDht >= 0) { sensores++; if (isnan(e.temperatura) || isnan(e.humedadAire)) fallas++; }
  // Sonda de suelo existente: cuenta y revisa.
  if (c.pinSuelo >= 0) { sensores++; if (isnan(e.humedadSuelo)) fallas++; }
  // Calidad: buena sin fallas, mala si fallaron todos, dudosa en otro caso.
  lectura["calidad"] = fallas == 0 ? "buena" : (fallas >= sensores ? "mala" : "dudosa");
  // Modo: manual si algún actuador está en manual.
  lectura["modo"] = (vigente(e.bombaManualHasta) || vigente(e.ventiladorManualHasta)) ? "manual" : "automatico";
  // Mediciones.
  JsonObject m = lectura["mediciones"].to<JsonObject>();
  // Temperatura y humedades (null sin dato).
  ponerNumero(m, "temperatura", e.temperatura, 1);
  ponerNumero(m, "humedad_ambiente", e.humedadAire, 1);
  ponerNumero(m, "humedad_sustrato", e.humedadSuelo, 1);
  // Sin sensor de luz, CO2 ni radiación en la DevKit: null.
  m["luz"] = nullptr;
  m["co2"] = nullptr;
  m["radiacion"] = nullptr;
  // Actuadores.
  JsonObject a = lectura["actuadores"].to<JsonObject>();
  // Bomba y ventilador según la tabla (null si la zona no los tiene).
  ponerActuador(a, "bomba", c.releBomba);
  ponerActuador(a, "ventilador", c.releVentilador);
  // No hay luces LED conectadas: null.
  a["luces"] = nullptr;
  // Respuesta.
  JsonDocument respuesta;
  // Envía y muestra el resultado.
  if (llamarRpc("registrar_lectura", cuerpo, respuesta)) {
    // "guardado" o "duplicado".
    Serial.printf("[nube] %s %s\n", c.nombre, respuesta["estado"] | "?");
  }
}

// Confirma una orden en Supabase.
void confirmarOrden(const char* id, const char* resultado, const char* detalle) {
  // Cuerpo.
  JsonDocument cuerpo;
  // Clave del controlador.
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  // Orden que se confirma.
  cuerpo["p_id_comando"] = id;
  // ejecutado, rechazado, caducado o duplicado.
  cuerpo["p_resultado"] = resultado;
  // Real o simulado según el modo.
  cuerpo["p_origen"] = ORIGEN;
  // Explicación corta.
  cuerpo["p_detalle"] = detalle;
  // Respuesta.
  JsonDocument respuesta;
  // Envía.
  if (llamarRpc("confirmar_comando", cuerpo, respuesta)) {
    // Muestra la confirmación.
    Serial.printf("[orden] %s -> %s (%s)\n", id, resultado, detalle);
  }
}

// Busca el índice de una zona por su nombre; -1 si no existe.
int buscarZona(const char* nombre) {
  // Recorre la tabla.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Compara nombres.
    if (strcmp(ZONAS[z].nombre, nombre) == 0) return z;
  }
  // No encontrada.
  return -1;
}

// Pregunta las órdenes pendientes y las ejecuta.
void atenderOrdenes() {
  // Cuerpo: solo la clave.
  JsonDocument cuerpo;
  // Clave del controlador.
  cuerpo["p_clave"] = DISPOSITIVO_CLAVE;
  // Respuesta: lista de órdenes.
  JsonDocument respuesta;
  // Si falla, se reintenta en el siguiente ciclo.
  if (!llamarRpc("comandos_pendientes", cuerpo, respuesta)) return;
  // Recorre las órdenes.
  for (JsonObject orden : respuesta.as<JsonArray>()) {
    // Datos de la orden.
    const char* id = orden["id_comando"] | "";
    // Zona.
    const char* zona = orden["zona"] | "";
    // Actuador: bomba, ventilador o luces.
    const char* actuador = orden["actuador"] | "";
    // encendido o apagado.
    const char* pedido = orden["estado_solicitado"] | "";
    // Vencimiento.
    const char* caduca = orden["caduca_en"] | "";
    // La informa.
    Serial.printf("[orden] recibida %s: %s/%s -> %s\n", id, zona, actuador, pedido);
    // Repetida: no se vuelve a ejecutar.
    if (yaProcesado(String(id))) { confirmarOrden(id, "duplicado", "orden ya procesada"); continue; }
    // La recuerda.
    recordarId(String(id));
    // Vencida: no se ejecuta.
    time_t limite = isoASegundos(caduca);
    // Compara con la hora actual.
    if (limite == 0 || time(nullptr) > limite) { confirmarOrden(id, "caducado", "la orden llego vencida"); continue; }
    // Busca la zona.
    int z = buscarZona(zona);
    // Zona desconocida.
    if (z < 0) { confirmarOrden(id, "rechazado", "zona desconocida"); continue; }
    // ¿Se pide encender?
    bool encender = strcmp(pedido, "encendido") == 0;
    // Relé que corresponde (o -1).
    int rele = -1;
    // Bomba.
    if (strcmp(actuador, "bomba") == 0) rele = ZONAS[z].releBomba;
    // Ventilador.
    else if (strcmp(actuador, "ventilador") == 0) rele = ZONAS[z].releVentilador;
    // Luces u otro: esta placa no tiene ese actuador en esa zona.
    if (rele < 0) { confirmarOrden(id, "rechazado", "esa zona no tiene ese actuador conectado"); continue; }
    // Intenta el cambio (una bomba en descanso no enciende).
    if (!cambiarRele(rele, encender, "orden de la web")) {
      // No se pudo.
      confirmarOrden(id, "rechazado", "bomba en descanso de seguridad, intenta en 30 s");
      continue;
    }
    // Modo manual por 2 minutos para ese actuador.
    if (strcmp(actuador, "bomba") == 0) estado[z].bombaManualHasta = millis() + MANUAL_MS;
    // Ventilador.
    else estado[z].ventiladorManualHasta = millis() + MANUAL_MS;
    // Confirma con detalle claro.
    confirmarOrden(id, "ejecutado", encender ? "encendido en modo manual por 2 min (bomba max 20 s)" : "apagado en modo manual por 2 min");
  }
}

// ---------------------------------------------------------------------------
// WiFi y hora
// ---------------------------------------------------------------------------

// Inicia la conexión WiFi sin bloquear (la reconexión es automática).
void iniciarWifi() {
  // Modo estación.
  WiFi.mode(WIFI_STA);
  // Reconexión automática.
  WiFi.setAutoReconnect(true);
  // Inicia la conexión.
  WiFi.begin(WIFI_SSID, WIFI_CLAVE);
  // Lo informa.
  Serial.printf("[wifi] conectando a \"%s\" (el control local funciona igual sin WiFi)\n", WIFI_SSID);
}

// Pide la hora UTC por NTP (sin bloquear: la hora llega en segundo plano).
void pedirHora() {
  // UTC, sin horario de verano.
  configTime(0, 0, "pool.ntp.org", "time.google.com");
}

// Muestra en el Monitor Serie un resumen de las 3 zonas.
void imprimirResumen() {
  // Recorre las zonas.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Estado.
    const EstadoZona& e = estado[z];
    // Una línea por zona (nan = sin dato).
    Serial.printf("[%-9s] T=%5.1f C  HR=%5.1f %%  suelo=%5.1f %% (crudo %4d)\n",
                  ZONAS[z].nombre, e.temperatura, e.humedadAire, e.humedadSuelo, e.crudoSuelo);
  }
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

// setup(): una vez al encender.
void setup() {
  // PRIMERO los relés en apagado, para que nada se encienda al arrancar.
  for (int i = 0; i < 4; i++) {
    // Estado lógico apagado.
    releEncendido[i] = false;
    // Escribe el nivel de "apagado" antes de configurar como salida.
    aplicarRele(i);
    // Configura como salida.
    pinMode(PINES_RELE[i], OUTPUT);
    // Vuelve a escribir "apagado".
    aplicarRele(i);
  }
  // Marca qué relés son bombas según la tabla de zonas.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Si la zona tiene bomba, ese relé es de bomba.
    if (ZONAS[z].releBomba >= 0) releEsBomba[ZONAS[z].releBomba] = true;
  }
  // Monitor Serie.
  Serial.begin(115200);
  // UART hacia la CYD: solo TX (RX = -1, no se usa).
  Serial2.begin(115200, SERIAL_8N1, -1, PIN_UART_TX);
  // Pequeña pausa para abrir el monitor.
  delay(300);
  // LED de estado.
  pinMode(PIN_LED_ESTADO, OUTPUT);
  // Alimentación de las sondas: salida, apagada.
  pinMode(PIN_ALIM_SUELO, OUTPUT);
  // Apagada.
  digitalWrite(PIN_ALIM_SUELO, LOW);
  // ADC de 12 bits (0..4095).
  analogReadResolution(12);
  // Rango de 0 a ~3,3 V.
  analogSetAttenuation(ADC_11db);
  // Crea los DHT22 de las zonas que lo tienen.
  for (int z = 0; z < NUM_ZONAS; z++) {
    // Solo si hay pin.
    if (ZONAS[z].pinDht >= 0) {
      // Crea el objeto del sensor.
      sensoresDht[z] = new DHT(ZONAS[z].pinDht, DHT22);
      // Lo inicia.
      sensoresDht[z]->begin();
    }
  }
  // Título.
  Serial.println("\n=== BAJOTERRA - Controlador v1 (3 zonas) ===");
  // Modo y dispositivo.
  Serial.printf("[config] modo: %s | datos: %s | dispositivo: %s\n", MODO_WOKWI ? "WOKWI" : "placa fisica", ORIGEN, DISPOSITIVO_ID);
  // HTTPS: sin verificar certificado (limitación conocida).
  tls.setInsecure();
  // Reutiliza la conexión entre peticiones (más rápido).
  http.setReuse(true);
  // Tiempo máximo de espera.
  http.setTimeout(ESPERA_HTTP_MS);
  // WiFi y hora en segundo plano.
  iniciarWifi();
  // Pide la hora.
  pedirHora();
}

// loop(): se repite sin parar.
void loop() {
  // Momento actual.
  unsigned long ahora = millis();
  // Seguridad de las bombas en cada vuelta.
  vigilarBombas();
  // ¿Hay WiFi?
  bool conectado = WiFi.status() == WL_CONNECTED;
  // LED: fijo con WiFi, parpadeo de 1 Hz sin WiFi.
  digitalWrite(PIN_LED_ESTADO, conectado ? HIGH : ((ahora / 500) % 2 ? HIGH : LOW));
  // Sensores + control cada 3 s.
  if (ultimoSensores == 0 || ahora - ultimoSensores >= INTERVALO_SENSORES_MS) {
    // Anota el momento.
    ultimoSensores = ahora;
    // Lee.
    leerSensores();
    // Decide.
    controlar();
    // Resumen en el monitor.
    imprimirResumen();
  }
  // Pantalla cada 2 s.
  if (ahora - ultimaPantalla >= INTERVALO_PANTALLA_MS) {
    // Anota el momento.
    ultimaPantalla = ahora;
    // Envía la línea.
    enviarPantalla();
  }
  // Sin WiFi no hay nube: el control local ya se hizo.
  if (!conectado) { delay(20); return; }
  // Si aún no hay hora, la vuelve a pedir cada 15 s.
  if (!horaValida()) {
    // ¿Toca reintentar?
    if (ahora - ultimoIntentoHora >= 15000) { ultimoIntentoHora = ahora; pedirHora(); Serial.println("[hora] esperando hora NTP..."); }
    // Sin hora no se envían lecturas.
    delay(20);
    return;
  }
  // Lecturas a Supabase cada 15 s (la primera apenas hay hora).
  if (ultimaNube == 0 || ahora - ultimaNube >= INTERVALO_NUBE_MS) {
    // Anota el momento.
    ultimaNube = ahora;
    // Una lectura por zona.
    for (int z = 0; z < NUM_ZONAS; z++) enviarLecturaZona(z);
  }
  // Órdenes cada 5 s.
  if (millis() - ultimasOrdenes >= INTERVALO_ORDENES_MS) {
    // Anota el momento.
    ultimasOrdenes = millis();
    // Atiende.
    atenderOrdenes();
  }
  // Pausa corta.
  delay(20);
}
