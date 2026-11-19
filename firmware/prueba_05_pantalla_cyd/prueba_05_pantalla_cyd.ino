// ============================================================================
// BAJOTERRA - Prueba 05: pantalla de la placa CYD (ESP32-2432S028, "Cheap Yellow Display").
// Esta placa ES una ESP32 con pantalla de 2,8" (controlador ILI9341, 320x240) integrada.
// Qué hace:
//   - Dibuja la pantalla del invernadero: título y una tarjeta por zona (árida, húmeda, selvática) con valores de ejemplo.
//   - Lee el sensor de luz (LDR) que trae la placa en GPIO 34 y lo muestra.
//   - Escucha el UART en GPIO 22 (conector P3 o CN1, el mismo pin del código antiguo del equipo) y muestra la última línea recibida: así se prueba el cable que vendrá
//     desde la ESP32 DevKit (en esta prueba los valores de las zonas son FIJOS, de ejemplo).
//
// Placa en Arduino IDE: "ESP32 Dev Module". Bibliotecas: "Adafruit ILI9341" y "Adafruit GFX Library".
// Si la pantalla queda en blanco, tu placa puede ser la versión con controlador ST7789: avísame y cambio la biblioteca.
// ============================================================================

// Bus SPI de la ESP32.
#include <SPI.h>
// Gráficos y controlador de la pantalla.
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// ---------------------------------------------------------------------------
// Pines de la CYD (fijos en la placa)
// ---------------------------------------------------------------------------
// Pantalla en el bus HSPI.
const int TFT_SCK = 14, TFT_MISO = 12, TFT_MOSI = 13, TFT_CS = 15, TFT_DC = 2;
// Luz de fondo de la pantalla.
const int TFT_LUZ_FONDO = 21;
// Sensor de luz (LDR) integrado.
const int PIN_LDR = 34;
// LED RGB integrado (se enciende en LOW): rojo, verde, azul.
const int LED_R = 4, LED_G = 16, LED_B = 17;
// UART que recibirá datos de la DevKit: RX en GPIO 22 (conector P3 o CN1). TX no se usa (-1).
const int UART_RX = 22;

// Bus HSPI propio para la pantalla.
SPIClass spiPantalla(HSPI);
// Objeto de la pantalla: bus, DC, CS (sin pin de reset: -1).
Adafruit_ILI9341 tft(&spiPantalla, TFT_DC, TFT_CS, -1);

// ---------------------------------------------------------------------------
// Colores (formato RGB565) y datos de las zonas
// ---------------------------------------------------------------------------
// Fondo casi negro verdoso (igual que la web).
const uint16_t COLOR_FONDO = 0x0841;
// Superficie de las tarjetas.
const uint16_t COLOR_TARJETA = 0x18E3;
// Texto principal y secundario.
const uint16_t COLOR_TEXTO = 0xEF7D;
const uint16_t COLOR_SUAVE = 0x9CF3;
// Verde de marca.
const uint16_t COLOR_VERDE = 0x4F2F;

// Una zona en pantalla: nombre, color de acento y valores de ejemplo (NAN = sin sensor).
struct ZonaPantalla {
  // Nombre corto.
  const char* nombre;
  // Color de acento (ámbar, celeste, lima).
  uint16_t color;
  // Temperatura (°C), humedad del aire (%) y del suelo (%) de EJEMPLO.
  float temperatura, humedadAire, humedadSuelo;
};

// Valores fijos de ejemplo; en la fase 4 llegarán por UART desde la DevKit.
ZonaPantalla zonas[3] = {
  {"ARIDA",     0xFD20, 32.1, 25.0, 18.0},
  {"HUMEDA",    0x3DDF, 24.0, 85.0, 70.0},
  {"SELVATICA", 0xA7E6, NAN,  NAN,  65.0},
};

// Última línea recibida por el UART y momento en que llegó.
String ultimaLinea = "";
unsigned long ultimaLineaMs = 0;
// Texto que se va armando con los caracteres que llegan.
String lineaEnCurso = "";
// Momento del último refresco de la parte dinámica.
unsigned long ultimoRefresco = 0;

// ---------------------------------------------------------------------------
// Dibujo
// ---------------------------------------------------------------------------

// Escribe un valor con unidad, o "--" si no hay dato (nunca se muestra 0 por falta de dato).
void escribirValor(float valor, const char* unidad, int decimales) {
  // Sin dato.
  if (isnan(valor)) { tft.print("--"); return; }
  // Número con los decimales pedidos y su unidad.
  tft.print(valor, decimales);
  tft.print(unidad);
}

// Dibuja la parte fija de la pantalla (título y marcos de las tarjetas). Se hace una sola vez para evitar parpadeo.
void dibujarFijo() {
  // Fondo completo.
  tft.fillScreen(COLOR_FONDO);
  // Título.
  tft.setTextColor(COLOR_VERDE);
  tft.setTextSize(2);
  tft.setCursor(8, 6);
  tft.print("BAJOTERRA");
  // Subtítulo.
  tft.setTextColor(COLOR_SUAVE);
  tft.setTextSize(1);
  tft.setCursor(130, 12);
  tft.print("Prueba 05 - valores de EJEMPLO");
  // Tres tarjetas (una por zona), lado a lado.
  for (int i = 0; i < 3; i++) {
    // Posición horizontal de la tarjeta.
    int x = 6 + i * 104;
    // Fondo de la tarjeta con esquinas redondeadas.
    tft.fillRoundRect(x, 30, 100, 150, 8, COLOR_TARJETA);
    // Franja superior de color de la zona.
    tft.fillRoundRect(x, 30, 100, 6, 3, zonas[i].color);
    // Nombre de la zona.
    tft.setTextColor(zonas[i].color);
    tft.setTextSize(1);
    tft.setCursor(x + 8, 44);
    tft.print(zonas[i].nombre);
    // Rótulos de cada medición.
    tft.setTextColor(COLOR_SUAVE);
    tft.setCursor(x + 8, 62);  tft.print("Temperatura");
    tft.setCursor(x + 8, 100); tft.print("Humedad aire");
    tft.setCursor(x + 8, 138); tft.print("Humedad suelo");
  }
}

// Dibuja los valores de cada zona y la barra inferior (luz y UART).
void dibujarDinamico() {
  // Valores de cada zona.
  for (int i = 0; i < 3; i++) {
    // Posición horizontal de la tarjeta.
    int x = 6 + i * 104;
    // Texto grande; el color de fondo borra el valor anterior sin parpadeo.
    tft.setTextColor(COLOR_TEXTO, COLOR_TARJETA);
    tft.setTextSize(2);
    // Temperatura.
    tft.setCursor(x + 8, 74);  escribirValor(zonas[i].temperatura, "C ", 1);
    // Humedad del aire.
    tft.setCursor(x + 8, 112); escribirValor(zonas[i].humedadAire, "% ", 0);
    // Humedad del suelo.
    tft.setCursor(x + 8, 150); escribirValor(zonas[i].humedadSuelo, "% ", 0);
  }
  // Barra inferior: luz (valor crudo del LDR; aún sin calibrar, no son lux).
  tft.setTextSize(1);
  tft.setTextColor(COLOR_SUAVE, COLOR_FONDO);
  tft.setCursor(8, 190);
  tft.printf("Luz (LDR crudo 0-4095): %4d   ", analogRead(PIN_LDR));
  // Estado del UART: última línea recibida (recortada) o aviso de que no llega nada.
  tft.setCursor(8, 206);
  if (ultimaLinea.length() == 0) {
    tft.print("UART (GPIO22): sin datos todavia                    ");
  } else {
    tft.printf("UART: hace %lus                                     ", (millis() - ultimaLineaMs) / 1000);
    tft.setCursor(8, 220);
    tft.print(ultimaLinea.substring(0, 50));
    tft.print("                                                  ");
  }
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

// setup(): una vez al encender.
void setup() {
  // Monitor Serie (por el USB de la CYD).
  Serial.begin(115200);
  // UART2 para recibir de la DevKit: 115200 baudios, 8N1, RX = 22, sin TX.
  Serial2.begin(115200, SERIAL_8N1, UART_RX, -1);
  // LED RGB apagado (HIGH = apagado).
  pinMode(LED_R, OUTPUT); digitalWrite(LED_R, HIGH);
  pinMode(LED_G, OUTPUT); digitalWrite(LED_G, HIGH);
  pinMode(LED_B, OUTPUT); digitalWrite(LED_B, HIGH);
  // Enciende la luz de fondo de la pantalla.
  pinMode(TFT_LUZ_FONDO, OUTPUT);
  digitalWrite(TFT_LUZ_FONDO, HIGH);
  // Inicia el bus HSPI con los pines de la pantalla.
  spiPantalla.begin(TFT_SCK, TFT_MISO, TFT_MOSI, TFT_CS);
  // Inicia la pantalla.
  tft.begin();
  // Horizontal (320 x 240).
  tft.setRotation(1);
  // Colores invertidos: el código antiguo del equipo lo necesitaba en esta placa. Si se ve en negativo, pon false.
  tft.invertDisplay(true);
  // Dibuja la parte fija.
  dibujarFijo();
  // Resolución analógica de 12 bits para el LDR.
  analogReadResolution(12);
  // Mensaje por USB.
  Serial.println("Prueba 05: pantalla lista.");
}

// loop(): se repite sin parar.
void loop() {
  // Lee los caracteres que lleguen por el UART y arma líneas completas.
  while (Serial2.available()) {
    // Un carácter.
    char c = Serial2.read();
    // Fin de línea: guarda la línea completa.
    if (c == '\n') {
      ultimaLinea = lineaEnCurso;
      ultimaLineaMs = millis();
      lineaEnCurso = "";
      // También la muestra por el Monitor Serie.
      Serial.printf("UART: %s\n", ultimaLinea.c_str());
    // Ignora retornos de carro.
    } else if (c != '\r') {
      // Agrega el carácter, con un límite para no gastar memoria si llega basura.
      if (lineaEnCurso.length() < 512) lineaEnCurso += c;
    }
  }
  // Refresca la parte dinámica una vez por segundo.
  if (millis() - ultimoRefresco >= 1000) {
    ultimoRefresco = millis();
    dibujarDinamico();
  }
}
