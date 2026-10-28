// ============================================================================
// BAJOTERRA - Pantalla v1 (placa CYD ESP32-2432S028).
//
// Qué hace:
//  1. Recibe por UART (GPIO 22) las líneas JSON que envía el controlador (ESP32 DevKit, GPIO 17) cada 2 s:
//       {"wifi":true,"origen":"real","hora":"2026-10-28T15:04:05Z",
//        "zonas":[{"n":"arida","t":31.2,"ha":35,"hs":40,"b":null,"v":"apagado","m":false}, ...]}
//  2. Muestra una zona a la vez (árida -> húmeda -> selvática, cada 4 s): temperatura, humedad del aire,
//     humedad del suelo y el estado de la bomba y del ventilador.
//  3. Si los datos dejan de llegar, lo dice en pantalla ("SIN DATOS NUEVOS") y pinta los valores en gris:
//     nunca muestra un dato viejo como si fuera actual. Un valor ausente se muestra como "--" (nunca 0).
//  4. Si los datos son simulados (Wokwi o pruebas), la pantalla dice "SIMULADO".
//  5. LED RGB de la placa: verde = datos al día, rojo = sin datos nuevos.
//
// Para probar SIN la DevKit: abre el Monitor Serie (115200) y pega una línea JSON como la de arriba.
//
// Ideas tomadas del código antiguo del equipo (Codigo_pantalla): diseño con tarjetas grises, banner de color
// por zona, rotación automática entre zonas, invertDisplay(true) y el pin RX 22. Se cambió el formato de
// texto con comas por JSON (el mismo que ya envía el controlador) y la biblioteca TFT_eSPI por las de Adafruit,
// que no necesitan editar archivos de configuración de la biblioteca.
//
// Placa: "ESP32 Dev Module". Bibliotecas: "Adafruit GFX Library", "Adafruit ILI9341"
// (o "Adafruit ST7735 and ST7789 Library" si PANTALLA_ST7789 = 1) y "ArduinoJson" (v7).
// ============================================================================

// Configuración (tipo de pantalla, pines y tiempos).
#include "config_pantalla.h"
// Bus SPI.
#include <SPI.h>
// Gráficos comunes (texto, rectángulos).
#include <Adafruit_GFX.h>
// Biblioteca del controlador de pantalla elegido.
#if PANTALLA_ST7789
// Pantallas ST7789 (CYD de 2 puertos USB).
#include <Adafruit_ST7789.h>
// Pantallas ILI9341.
#else
// Biblioteca ILI9341.
#include <Adafruit_ILI9341.h>
// Fin de la condición.
#endif
// Lectura de JSON (ArduinoJson 7).
#include <ArduinoJson.h>

// Bus HSPI propio para la pantalla.
SPIClass spiPantalla(HSPI);
// Objeto de la pantalla (bus, CS, DC y sin pin de reset = -1).
#if PANTALLA_ST7789
// Pantalla ST7789.
Adafruit_ST7789 tft(&spiPantalla, TFT_CS, TFT_DC, -1);
// Pantalla ILI9341.
#else
// Pantalla ILI9341.
Adafruit_ILI9341 tft(&spiPantalla, TFT_DC, TFT_CS, -1);
// Fin de la condición.
#endif

// ---------------------------------------------------------------------------
// Colores (formato RGB565 de 16 bits)
// ---------------------------------------------------------------------------

// Fondo gris casi negro (como el código antiguo: 20,20,20).
const uint16_t C_FONDO = 0x10A2;
// Tarjetas gris oscuro (45,45,45).
const uint16_t C_TARJETA = 0x2965;
// Etiquetas en gris medio (180,180,180).
const uint16_t C_ETIQUETA = 0xB5B6;
// Valores apagados (datos viejos o ausentes).
const uint16_t C_APAGADO = 0x6B4D;
// Temperatura en rojo claro (255,100,100).
const uint16_t C_TEMP = 0xFB2C;
// Humedad del aire en celeste (0,200,255).
const uint16_t C_HUM = 0x065F;
// Humedad del suelo en ámbar (255,200,0).
const uint16_t C_SUELO = 0xFE40;
// Verde de "encendido" (0,150,0).
const uint16_t C_ON = 0x04A0;
// Rojo de "apagado" (180,0,0).
const uint16_t C_OFF = 0xB000;
// Blanco.
const uint16_t C_BLANCO = 0xFFFF;

// ---------------------------------------------------------------------------
// Datos recibidos
// ---------------------------------------------------------------------------

// Estado de un actuador según el controlador.
enum Actuador { NO_EXISTE, APAGADO, ENCENDIDO };

// Lo que la pantalla sabe de una zona.
struct ZonaPantalla {
  // Nombre que llega en el JSON ("arida", "humeda", "selvatica").
  const char* clave;
  // Título que se muestra.
  const char* titulo;
  // Color del banner.
  uint16_t color;
  // Temperatura (°C); NAN = sin dato.
  float temperatura;
  // Humedad del aire (%); NAN = sin dato.
  float humedadAire;
  // Humedad del suelo (%); NAN = sin dato.
  float humedadSuelo;
  // Bomba.
  Actuador bomba;
  // Ventilador.
  Actuador ventilador;
  // true si algún actuador está en modo manual (orden de la web).
  bool manual;
};

// Las 3 zonas: árida en ámbar, húmeda en azul, selvática en verde. Sin datos hasta que llegue el primer JSON.
ZonaPantalla zonas[3] = {
  // Árida.
  {"arida", "ZONA ARIDA", 0xC3A0, NAN, NAN, NAN, NO_EXISTE, NO_EXISTE, false},
  // Húmeda.
  {"humeda", "ZONA HUMEDA", 0x2B9F, NAN, NAN, NAN, NO_EXISTE, NO_EXISTE, false},
  // Selvática.
  {"selvatica", "ZONA SELVATICA", 0x2C64, NAN, NAN, NAN, NO_EXISTE, NO_EXISTE, false},
};

// ¿El controlador tiene WiFi?
bool wifiControlador = false;
// ¿Los datos son simulados? (true hasta saber lo contrario: más seguro).
bool datosSimulados = true;
// Momento (millis) en que llegó el último JSON válido; 0 = nunca.
unsigned long ultimoDatoMs = 0;

// Texto que se va armando con los caracteres del UART.
String lineaUart = "";
// Texto que se va armando con los caracteres del Monitor Serie (modo prueba).
String lineaUsb = "";

// Zona que se muestra ahora (0, 1 o 2).
int zonaActual = 0;
// Momento del último cambio de zona.
unsigned long ultimoCambioZona = 0;
// Momento del último refresco de valores.
unsigned long ultimoRefresco = 0;

// ---------------------------------------------------------------------------
// Lectura del JSON
// ---------------------------------------------------------------------------

// Lee un número del JSON: NAN si es null, no existe o no es número.
float numeroONan(JsonVariantConst valor) {
  // Solo acepta números.
  if (valor.is<float>()) return valor.as<float>();
  // Cualquier otra cosa: sin dato.
  return NAN;
}

// Convierte "encendido"/"apagado"/null en el estado del actuador.
Actuador leerActuador(JsonVariantConst valor) {
  // null o ausente: la zona no tiene ese actuador.
  if (!valor.is<const char*>()) return NO_EXISTE;
  // Texto "encendido".
  if (strcmp(valor.as<const char*>(), "encendido") == 0) return ENCENDIDO;
  // Cualquier otro texto se toma como apagado.
  return APAGADO;
}

// Procesa una línea JSON completa. Devuelve true si era válida.
bool procesarLinea(const String& linea) {
  // Documento JSON.
  JsonDocument doc;
  // Intenta leerlo.
  DeserializationError error = deserializeJson(doc, linea);
  // Línea dañada (por ejemplo, ruido en el cable): se ignora.
  if (error) {
    // Lo informa en el Monitor Serie.
    Serial.printf("[uart] linea ignorada (%s): %s\n", error.c_str(), linea.c_str());
    return false;
  }
  // Debe traer la lista de zonas.
  JsonArrayConst lista = doc["zonas"].as<JsonArrayConst>();
  // Sin lista: no es un mensaje del controlador.
  if (lista.isNull()) return false;
  // WiFi del controlador.
  wifiControlador = doc["wifi"] | false;
  // Origen: solo "real" se considera real.
  datosSimulados = strcmp(doc["origen"] | "simulado", "real") != 0;
  // Recorre las zonas recibidas.
  for (JsonObjectConst z : lista) {
    // Nombre de la zona.
    const char* nombre = z["n"] | "";
    // Busca esa zona en la tabla.
    for (int i = 0; i < 3; i++) {
      // ¿Coincide?
      if (strcmp(nombre, zonas[i].clave) == 0) {
        // Copia los valores (null = NAN).
        zonas[i].temperatura = numeroONan(z["t"]);
        // Humedad del aire.
        zonas[i].humedadAire = numeroONan(z["ha"]);
        // Humedad del suelo.
        zonas[i].humedadSuelo = numeroONan(z["hs"]);
        // Bomba.
        zonas[i].bomba = leerActuador(z["b"]);
        // Ventilador.
        zonas[i].ventilador = leerActuador(z["v"]);
        // Modo manual.
        zonas[i].manual = z["m"] | false;
      }
    }
  }
  // Anota cuándo llegó.
  ultimoDatoMs = millis();
  // Mensaje válido.
  return true;
}

// Junta caracteres de un puerto serie y procesa cada línea completa.
void leerPuerto(Stream& puerto, String& buffer) {
  // Mientras haya caracteres disponibles.
  while (puerto.available()) {
    // Lee un carácter.
    char c = (char)puerto.read();
    // Fin de línea: procesa lo acumulado.
    if (c == '\n') {
      // Quita espacios y '\r'.
      buffer.trim();
      // Solo si hay algo.
      if (buffer.length() > 0) procesarLinea(buffer);
      // Empieza una línea nueva.
      buffer = "";
    } else if (buffer.length() < 1024) {
      // Acumula (con límite, por si llega basura sin saltos de línea).
      buffer += c;
    } else {
      // Línea demasiado larga: se descarta.
      buffer = "";
    }
  }
}

// ---------------------------------------------------------------------------
// Dibujo
// ---------------------------------------------------------------------------

// true si llegó un dato hace poco.
bool datosAlDia() {
  // Nunca llegó nada, o pasó demasiado tiempo.
  return ultimoDatoMs != 0 && millis() - ultimoDatoMs < DATOS_VIEJOS_MS;
}

// Escribe un texto en una posición, tamaño y color.
void texto(int x, int y, uint8_t tam, uint16_t color, const char* t) {
  // Posición.
  tft.setCursor(x, y);
  // Tamaño.
  tft.setTextSize(tam);
  // Color (sin fondo: el fondo se borra antes con fillRect).
  tft.setTextColor(color);
  // Texto.
  tft.print(t);
}

// Dibuja las partes fijas: fondo, tarjetas y etiquetas (una vez, para evitar parpadeos).
void dibujarEsqueleto() {
  // Fondo general.
  tft.fillScreen(C_FONDO);
  // Tarjeta de temperatura (arriba a la izquierda).
  tft.fillRoundRect(10, 54, 145, 76, 8, C_TARJETA);
  // Etiqueta.
  texto(20, 62, 2, C_ETIQUETA, "Temp.");
  // Tarjeta de humedad del aire (arriba a la derecha).
  tft.fillRoundRect(165, 54, 145, 76, 8, C_TARJETA);
  // Etiqueta.
  texto(175, 62, 2, C_ETIQUETA, "Hum. aire");
  // Tarjeta de humedad del suelo (abajo a la izquierda).
  tft.fillRoundRect(10, 138, 145, 70, 8, C_TARJETA);
  // Etiqueta.
  texto(20, 146, 2, C_ETIQUETA, "Suelo");
  // Tarjeta de actuadores (abajo a la derecha).
  tft.fillRoundRect(165, 138, 145, 70, 8, C_TARJETA);
}

// Dibuja el banner de la zona actual (cambia cada 4 s).
void dibujarBanner() {
  // Zona actual.
  const ZonaPantalla& z = zonas[zonaActual];
  // Fondo del banner con el color de la zona.
  tft.fillRoundRect(10, 8, 300, 38, 6, z.color);
  // Título.
  texto(20, 19, 2, C_BLANCO, z.titulo);
  // Indicador de página: 1/3, 2/3, 3/3.
  char pagina[6];
  // Arma el texto.
  snprintf(pagina, sizeof(pagina), "%d/3", zonaActual + 1);
  // Lo escribe a la derecha.
  texto(282, 30, 1, C_BLANCO, pagina);
}

// Escribe un valor con unidad, o "--" si no hay dato.
void dibujarValor(int x, int y, float valor, int decimales, const char* unidad, uint16_t color) {
  // Borra el valor anterior tapándolo con el color de la tarjeta.
  tft.fillRect(x, y, 128, 26, C_TARJETA);
  // Datos viejos: todo en gris.
  uint16_t c = datosAlDia() ? color : C_APAGADO;
  // Sin dato.
  if (isnan(valor)) {
    // Muestra "--" (nunca 0).
    texto(x, y, 3, C_APAGADO, "--");
    return;
  }
  // Texto del número.
  char numero[12];
  // Con los decimales pedidos.
  snprintf(numero, sizeof(numero), "%.*f", decimales, valor);
  // Número grande.
  texto(x, y, 3, c, numero);
  // Unidad más pequeña, a continuación.
  tft.setTextSize(2);
  // Mismo color.
  tft.print(unidad);
}

// Dibuja una etiqueta de actuador: verde = ON, rojo = OFF, gris = la zona no lo tiene.
void dibujarActuador(int y, const char* nombre, Actuador estado) {
  // Borra la línea.
  tft.fillRect(172, y - 2, 132, 22, C_TARJETA);
  // Color de fondo según el estado.
  uint16_t fondo = estado == ENCENDIDO ? C_ON : (estado == APAGADO ? C_OFF : C_APAGADO);
  // Datos viejos: en gris (no se sabe el estado actual).
  if (!datosAlDia()) fondo = C_APAGADO;
  // Texto.
  char t[20];
  // "Bomba ON", "Bomba OFF" o "Bomba --".
  snprintf(t, sizeof(t), " %s %s ", nombre, estado == ENCENDIDO ? "ON" : (estado == APAGADO ? "OFF" : "--"));
  // Posición.
  tft.setCursor(175, y);
  // Tamaño mediano.
  tft.setTextSize(2);
  // Blanco sobre el color del estado.
  tft.setTextColor(C_BLANCO, fondo);
  // Escribe.
  tft.print(t);
}

// Dibuja la barra inferior: estado de los datos, WiFi del controlador y LDR de la placa.
void dibujarPie() {
  // Borra la barra.
  tft.fillRect(0, 214, 320, 26, C_FONDO);
  // Texto del estado.
  char t[48];
  // Sin datos nunca.
  if (ultimoDatoMs == 0) {
    // Esperando el primer mensaje.
    texto(10, 220, 1, C_OFF, "ESPERANDO DATOS DEL CONTROLADOR (cable GPIO22)");
    return;
  }
  // Segundos desde el último dato.
  unsigned long seg = (millis() - ultimoDatoMs) / 1000;
  // Datos al día o no.
  if (datosAlDia()) {
    // Ejemplo: "Dato hace 1 s | WiFi si | REAL"
    snprintf(t, sizeof(t), "Dato hace %lu s | WiFi %s | %s", seg, wifiControlador ? "si" : "no", datosSimulados ? "SIMULADO" : "REAL");
    // En gris claro.
    texto(10, 220, 1, C_ETIQUETA, t);
  } else {
    // Ejemplo: "SIN DATOS NUEVOS (hace 25 s)"
    snprintf(t, sizeof(t), "SIN DATOS NUEVOS (hace %lu s)", seg);
    // En rojo.
    texto(10, 220, 1, C_OFF, t);
  }
  // LDR: valor crudo (0-4095). Es luz RELATIVA, no lux: falta calibrarlo.
  snprintf(t, sizeof(t), "LDR %d", analogRead(PIN_LDR));
  // A la derecha.
  texto(260, 220, 1, C_ETIQUETA, t);
}

// Actualiza los valores de la zona actual.
void dibujarValores() {
  // Zona actual.
  const ZonaPantalla& z = zonas[zonaActual];
  // Temperatura con 1 decimal.
  dibujarValor(20, 92, z.temperatura, 1, "C", C_TEMP);
  // Humedad del aire sin decimales.
  dibujarValor(175, 92, z.humedadAire, 0, "%", C_HUM);
  // Humedad del suelo sin decimales.
  dibujarValor(20, 172, z.humedadSuelo, 0, "%", C_SUELO);
  // Bomba.
  dibujarActuador(148, "Bomba", z.bomba);
  // Ventilador.
  dibujarActuador(176, "Vent.", z.ventilador);
  // Marcas pequeñas en el banner: SIMULADO y MANUAL.
  tft.fillRect(190, 12, 88, 14, zonas[zonaActual].color);
  // Simulado.
  if (datosSimulados && ultimoDatoMs != 0) texto(190, 14, 1, C_BLANCO, "SIMULADO");
  // Manual.
  if (z.manual) texto(246, 14, 1, C_BLANCO, "MANUAL");
  // Pie.
  dibujarPie();
}

// Enciende el LED RGB: verde con datos al día, rojo sin datos.
void actualizarLed() {
  // ¿Datos al día?
  bool ok = datosAlDia();
  // Rojo (activo en LOW).
  digitalWrite(LED_R, ok ? HIGH : LOW);
  // Verde.
  digitalWrite(LED_G, ok ? LOW : HIGH);
  // Azul siempre apagado.
  digitalWrite(LED_B, HIGH);
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

// setup(): una vez al encender.
void setup() {
  // Monitor Serie (también sirve para pegar JSON de prueba).
  Serial.begin(115200);
  // UART desde la DevKit: solo RX en GPIO 22 (TX = -1, no se usa; así no choca con la luz de fondo en GPIO 21).
  Serial2.begin(UART_BAUDIOS, SERIAL_8N1, UART_RX, -1);
  // LED RGB como salidas.
  pinMode(LED_R, OUTPUT);
  // Verde.
  pinMode(LED_G, OUTPUT);
  // Azul.
  pinMode(LED_B, OUTPUT);
  // Luz de fondo encendida.
  pinMode(TFT_LUZ_FONDO, OUTPUT);
  // Encendida.
  digitalWrite(TFT_LUZ_FONDO, HIGH);
  // Bus SPI de la pantalla con sus pines.
  spiPantalla.begin(TFT_SCK, TFT_MISO, TFT_MOSI, TFT_CS);
  // Inicia la pantalla.
#if PANTALLA_ST7789
  // ST7789 de 240x320.
  tft.init(240, 320);
#else
  // ILI9341.
  tft.begin();
#endif
  // Horizontal (320x240), como el código antiguo.
  tft.setRotation(1);
  // Colores invertidos si la placa lo necesita.
  tft.invertDisplay(INVERTIR_COLORES);
  // Partes fijas.
  dibujarEsqueleto();
  // Banner de la primera zona.
  dibujarBanner();
  // Valores (todavía "--").
  dibujarValores();
  // LED en rojo hasta que lleguen datos.
  actualizarLed();
  // Mensaje de inicio.
  Serial.println("\n=== BAJOTERRA - Pantalla v1 === esperando JSON por GPIO22 (o pega uno aqui)");
}

// loop(): se repite sin parar (sin delay largos: no se pierden caracteres del UART).
void loop() {
  // Datos desde la DevKit.
  leerPuerto(Serial2, lineaUart);
  // Datos pegados en el Monitor Serie (modo prueba).
  leerPuerto(Serial, lineaUsb);
  // Momento actual.
  unsigned long ahora = millis();
  // ¿Toca cambiar de zona?
  if (ahora - ultimoCambioZona >= CAMBIO_ZONA_MS) {
    // Anota el momento.
    ultimoCambioZona = ahora;
    // Siguiente zona (0 -> 1 -> 2 -> 0).
    zonaActual = (zonaActual + 1) % 3;
    // Nuevo banner.
    dibujarBanner();
    // Fuerza el refresco de valores.
    ultimoRefresco = 0;
  }
  // ¿Toca refrescar los valores?
  if (ultimoRefresco == 0 || ahora - ultimoRefresco >= REFRESCO_MS) {
    // Anota el momento.
    ultimoRefresco = ahora;
    // Dibuja.
    dibujarValores();
    // LED.
    actualizarLed();
  }
}
