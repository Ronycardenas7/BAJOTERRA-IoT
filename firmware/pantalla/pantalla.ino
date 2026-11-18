/* ==================================================================
   BAJOTERRA · PANTALLA TÁCTIL CYD  (versión 3.1 final)
   ================================================================== */
#include <Arduino.h>
#include <SPI.h>
#include <TFT_eSPI.h>

#define CYD_BL      21
#define RX_MAESTRO  22
#define TX_MAESTRO  27
#define T_IRQ  36
#define T_MOSI 32
#define T_MISO 39
#define T_CLK  25
#define T_CS   33

const bool INVERTIR_COLORES = true;
const int  TS_MINX = 200, TS_MAXX = 3700, TS_MINY = 240, TS_MAXY = 3800;
const bool TACTIL_INV_X = false;
const bool TACTIL_INV_Y = false;
const int  PRESION_MIN  = 400;
const uint32_t SIN_CONEXION_MS = 6000;
const uint32_t VOLVER_INICIO_MS = 120000;

TFT_eSPI tft = TFT_eSPI();

struct DatosZona {
  char letra; const char* nombre; const char* corto; const char* planta; uint16_t acento;
  float temp, hr, suelo, uVent, tObj, sMin, sMax, hMin, hMax;
  int   riego, vent, estado, alarmas;
};
DatosZona zonas[3] = {
  {'A', "ARIDA",     "ARIDA",    "cactus",           0, -99,-99,-99,0, 24,15,35,20,40, 0,0,0,0},
  {'H', "TEMPLADA",  "TEMPLADA", "tagete/oreja oso", 0, -99,-99,-99,0, 22,30,50,40,60, 0,0,0,0},
  {'S', "SELVATICA", "SELVA",    "schefflera",       0, -99,-99,-99,0, 25,40,60,55,75, 0,0,0,0},
};

struct Boton { int x, y, w, h; };
uint16_t NEGRO, BLANCO, GRIS, GRIS_OSC, VERDE, AMARILLO, ROJO, AZUL, NARANJO, MARCO;

char     linea[400];
uint16_t pos = 0;
uint32_t lineasOk = 0, ultimaLinea = 0;
int      pantalla = -1;
bool     redibujarTodo = true, hayDatosNuevos = true;
uint32_t ultimoToque = 0, toastHasta = 0;
char     toastTxt[48] = "";
uint16_t toastColor = 0;

bool conectado() { return ultimaLinea != 0 && millis() - ultimaLinea <= SIN_CONEXION_MS; }
bool hayDatos(const DatosZona& z) { return conectado() && z.estado != 0 && z.temp > -90; }

uint16_t xptLeer(uint8_t cmd) {
  for (int i = 7; i >= 0; i--) {
    digitalWrite(T_MOSI, (cmd >> i) & 1);
    digitalWrite(T_CLK, HIGH); delayMicroseconds(2);
    digitalWrite(T_CLK, LOW);  delayMicroseconds(2);
  }
  uint16_t v = 0;
  for (int i = 11; i >= 0; i--) {
    digitalWrite(T_CLK, HIGH); delayMicroseconds(2);
    digitalWrite(T_CLK, LOW);  delayMicroseconds(2);
    v |= (uint16_t)digitalRead(T_MISO) << i;
  }
  return v;
}

bool leerTactil(int& rx, int& ry, int& z) {
  digitalWrite(T_CS, LOW);
  int z1 = xptLeer(0xB0), z2 = xptLeer(0xC0);
  z = z1 + 4095 - z2;
  if (z1 < 50 || z2 > 4050 || z < PRESION_MIN) { digitalWrite(T_CS, HIGH); return false; }
  xptLeer(0x90); int a1 = xptLeer(0x90), a2 = xptLeer(0x90);
  xptLeer(0xD0); int b1 = xptLeer(0xD0), b2 = xptLeer(0xD0);
  digitalWrite(T_CS, HIGH);
  rx = (a1 + a2) / 2;
  ry = (b1 + b2) / 2;
  return true;
}

bool procesarZona(char* seg) {
  char* c[14]; int n = 0; char* g;
  for (char* t = strtok_r(seg, ",", &g); t && n < 14; t = strtok_r(NULL, ",", &g)) c[n++] = t;
  if (n != 14) return false;
  for (int i = 0; i < 3; i++) {
    if (zonas[i].letra != c[0][0]) continue;
    DatosZona& z = zonas[i];
    z.temp = atof(c[1]);  z.hr = atof(c[2]);   z.suelo = atof(c[3]);
    z.riego = atoi(c[4]); z.vent = atoi(c[5]); z.estado = atoi(c[6]);
    z.uVent = atof(c[7]); z.tObj = atof(c[8]); z.sMin = atof(c[9]); z.sMax = atof(c[10]);
    z.hMin = atof(c[11]); z.hMax = atof(c[12]); z.alarmas = atoi(c[13]);
    return true;
  }
  return false;
}

void leerSerie() {
  while (Serial2.available()) {
    char ch = Serial2.read();
    if (ch == '\n') {
      linea[pos] = '\0';
      bool ok = false; char* g;
      for (char* seg = strtok_r(linea, ";", &g); seg; seg = strtok_r(NULL, ";", &g))
        if (procesarZona(seg)) ok = true;
      if (ok) { ultimaLinea = millis(); lineasOk++; hayDatosNuevos = true; }
      pos = 0;
    } else if (ch != '\r') {
      if (pos < sizeof(linea) - 1) linea[pos++] = ch; else pos = 0;
    }
  }
}

void enviar(const DatosZona& z, const char* cmd, const char* valor) {
  Serial2.printf("CMD,%c,%s,%s\n", z.letra, cmd, valor);
  Serial.printf("Enviado: CMD,%c,%s,%s\n", z.letra, cmd, valor);
}

void toast(const char* t, uint16_t color) {
  strncpy(toastTxt, t, sizeof(toastTxt) - 1);
  toastColor = color;
  toastHasta = millis() + 2500;
  hayDatosNuevos = true;
}

uint16_t colTemp(const DatosZona& z) {
  if (z.temp <= z.tObj) return VERDE;
  if (z.temp <= z.tObj + 2) return AMARILLO;
  return ROJO;
}
uint16_t colRango(float v, float lo, float hi) {
  if (v >= lo && v <= hi) return VERDE;
  if (v >= lo - 10 && v <= hi + 10) return AMARILLO;
  return ROJO;
}

void txt(const char* s, int x, int y, uint8_t tam, uint16_t col, uint8_t datum = TL_DATUM) {
  tft.setTextDatum(datum); tft.setTextSize(tam); tft.setTextColor(col);
  tft.drawString(s, x, y);
}
void txtf(int x, int y, uint8_t tam, uint16_t col, uint8_t datum, const char* fmt, ...) {
  char b[48]; va_list a; va_start(a, fmt); vsnprintf(b, sizeof(b), fmt, a); va_end(a);
  txt(b, x, y, tam, col, datum);
}

void barra(int x, int y, int w, int h, float v, float vmin, float vmax, float lo, float hi, uint16_t col) {
  auto px = [&](float val) { return x + (int)(constrain((val - vmin) / (vmax - vmin), 0.0f, 1.0f) * (w - 2)) + 1; };
  tft.fillRoundRect(x, y, w, h, h / 2, GRIS_OSC);
  if (hi > lo) tft.fillRect(px(lo), y + 1, max(1, px(hi) - px(lo)), h - 2, tft.color565(0, 90, 45));
  if (v > -90) {
    int xv = px(v);
    tft.fillRoundRect(x, y, max(h, xv - x), h, h / 2, col);
    tft.fillTriangle(xv, y - 2, xv - 4, y - 7, xv + 4, y - 7, BLANCO);
  }
  tft.drawFastVLine(px(lo), y - 2, h + 4, BLANCO);
  if (hi > lo) tft.drawFastVLine(px(hi), y - 2, h + 4, BLANCO);
}

void pastilla(int x, int y, int w, int h, const char* t, uint16_t fondo, uint16_t letra) {
  tft.fillRoundRect(x, y, w, h, h / 2, fondo);
  txt(t, x + w / 2, y + h / 2 + 1, 1, letra, MC_DATUM);
}

void barraSuperior(const char* titulo, uint16_t col) {
  tft.fillRect(0, 0, 320, 26, NEGRO);
  txt(titulo, 8, 6, 2, col);
  bool ok = conectado();
  tft.fillCircle(256, 13, 4, ok ? VERDE : ROJO);
  txt(ok ? "ENLACE OK" : "SIN ENLACE", 264, 13, 1, ok ? VERDE : ROJO, ML_DATUM);
  tft.drawFastHLine(0, 26, 320, MARCO);
}

void barraInferior(const char* ayuda) {
  tft.fillRect(0, 214, 320, 26, NEGRO);
  tft.drawFastHLine(0, 213, 320, MARCO);
  if (millis() < toastHasta) txt(toastTxt, 8, 227, 1, toastColor, ML_DATUM);
  else txt(ayuda, 8, 227, 1, GRIS, ML_DATUM);
  txtf(314, 227, 1, GRIS, MR_DATUM, "RX %lu", (unsigned long)lineasOk);
}

const int CARD_W = 102, CARD_Y = 32, CARD_H = 176;
int cardX(int i) { return 4 + i * 106; }

void dibujarTarjeta(int i) {
  DatosZona& z = zonas[i];
  int x = cardX(i), y = CARD_Y, cx = x + CARD_W / 2;
  bool d = hayDatos(z);
  uint16_t borde = (d && z.alarmas) ? ROJO : z.acento;

  tft.fillRoundRect(x, y, CARD_W, CARD_H, 8, NEGRO);
  tft.drawRoundRect(x, y, CARD_W, CARD_H, 8, borde);
  tft.drawRoundRect(x + 1, y + 1, CARD_W - 2, CARD_H - 2, 7, borde);
  tft.fillRoundRect(x, y, CARD_W, 24, 8, z.acento);
  tft.fillRect(x, y + 16, CARD_W, 8, z.acento);
  txt(z.corto, cx, y + 13, 2, NEGRO, MC_DATUM);

  if (!d) {
    if (z.estado == 2) {
      txt("MANUAL", cx, y + 76, 2, NARANJO, MC_DATUM);
      txt("nodo apagado", cx, y + 100, 1, GRIS, MC_DATUM);
    } else {
      txt("SIN", cx, y + 68, 2, GRIS, MC_DATUM);
      txt("DATOS", cx, y + 88, 2, GRIS, MC_DATUM);
      txt("revisar nodo", cx, y + 110, 1, GRIS, MC_DATUM);
    }
  } else {
    txt("TEMP", x + 8, y + 30, 1, GRIS);
    txtf(cx, y + 50, 3, colTemp(z), MC_DATUM, "%.1f", z.temp);
    txtf(cx, y + 70, 1, GRIS, MC_DATUM, "ventila >%.1fC", z.tObj);
    tft.drawFastHLine(x + 8, y + 78, CARD_W - 16, MARCO);
    txt("SUELO", x + 8, y + 86, 1, GRIS);
    txtf(x + CARD_W - 8, y + 83, 2, colRango(z.suelo, z.sMin, z.sMax), TR_DATUM, "%.0f%%", z.suelo);
    barra(x + 8, y + 105, CARD_W - 16, 6, z.suelo, 0, 100, z.sMin, z.sMax, colRango(z.suelo, z.sMin, z.sMax));
    txt("AIRE", x + 8, y + 117, 1, GRIS);
    txtf(x + CARD_W - 8, y + 114, 2, colRango(z.hr, z.hMin, z.hMax), TR_DATUM, "%.0f%%", z.hr);
    barra(x + 8, y + 136, CARD_W - 16, 6, z.hr, 0, 100, z.hMin, z.hMax, colRango(z.hr, z.hMin, z.hMax));
  }
  pastilla(x + 6,  y + 146, 43, 14, "VENT",  z.vent ? VERDE : GRIS_OSC, z.vent ? NEGRO : GRIS);
  pastilla(x + 53, y + 146, 43, 14, "RIEGO", z.riego ? AZUL : GRIS_OSC, z.riego ? NEGRO : GRIS);
  const char* e = "AUTO"; uint16_t ce = GRIS;
  if (z.estado == 2) { e = "MANUAL"; ce = NARANJO; }
  if (d && (z.alarmas & 1)) { e = "! RIEGO"; ce = ROJO; }
  else if (d && (z.alarmas & 6)) { e = "! SENSOR"; ce = ROJO; }
  txt(e, cx, y + CARD_H - 4, 1, ce, BC_DATUM);
}

void dibujarInicio(bool todo) {
  if (todo) tft.fillScreen(NEGRO);
  barraSuperior("BAJOTERRA", BLANCO);
  for (int i = 0; i < 3; i++) dibujarTarjeta(i);
  barraInferior("Toca una zona para ver el detalle");
}

const Boton B_VOLVER = {0, 0, 70, 28},  B_MENOS = {10, 104, 34, 22}, B_MAS = {120, 104, 34, 22};
const Boton B_MODO = {4, 178, 100, 32}, B_VENT = {110, 178, 100, 32}, B_RIEGO = {216, 178, 100, 32};
bool dentro(const Boton& b, int x, int y) { return x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h; }

void boton(const Boton& b, const char* titulo, const char* valor, uint16_t fondo, uint16_t letra, bool activo) {
  tft.fillRoundRect(b.x, b.y, b.w, b.h, 8, activo ? fondo : NEGRO);
  tft.drawRoundRect(b.x, b.y, b.w, b.h, 8, activo ? fondo : GRIS_OSC);
  txt(titulo, b.x + b.w / 2, b.y + 8,  1, activo ? letra : GRIS, MC_DATUM);
  txt(valor,  b.x + b.w / 2, b.y + 22, 2, activo ? letra : GRIS, MC_DATUM);
}

void panel(int x, int y, int w, int h, const char* titulo, uint16_t col) {
  tft.fillRoundRect(x, y, w, h, 8, NEGRO);
  tft.drawRoundRect(x, y, w, h, 8, col);
  txt(titulo, x + 8, y + 6, 1, GRIS);
}

void dibujarDetalle(int i, bool todo) {
  DatosZona& z = zonas[i];
  bool d = hayDatos(z), manual = z.estado == 2;
  if (todo) tft.fillScreen(NEGRO);

  tft.fillRect(0, 0, 320, 27, NEGRO);
  tft.fillRoundRect(4, 3, 60, 21, 6, GRIS_OSC);
  txt("< INICIO", 34, 14, 1, BLANCO, MC_DATUM);
  txt(z.nombre, 72, 6, 2, z.acento);
  pastilla(250, 5, 66, 17, manual ? "MANUAL" : (z.estado == 1 ? "AUTO" : "SIN DATOS"),
           manual ? NARANJO : (z.estado == 1 ? VERDE : GRIS_OSC), NEGRO);
  tft.drawFastHLine(0, 27, 320, MARCO);

  panel(4, 32, 154, 100, "TEMPERATURA", z.acento);
  if (d) { char b[10]; snprintf(b, sizeof(b), "%.1f", z.temp);
           txt(b, 12, 46, 4, colTemp(z)); txt("C", 14 + 24 * strlen(b), 46, 2, colTemp(z)); }
  else txt("--", 12, 46, 4, GRIS);
  barra(12, 88, 138, 7, d ? z.temp : -99, 10, 40, 10, z.tObj, d ? colTemp(z) : GRIS);
  tft.fillRoundRect(B_MENOS.x, B_MENOS.y, B_MENOS.w, B_MENOS.h, 6, GRIS_OSC);
  tft.fillRoundRect(B_MAS.x, B_MAS.y, B_MAS.w, B_MAS.h, 6, GRIS_OSC);
  txt("-", B_MENOS.x + 17, B_MENOS.y + 12, 2, BLANCO, MC_DATUM);
  txt("+", B_MAS.x + 17, B_MAS.y + 12, 2, BLANCO, MC_DATUM);
  txt("objetivo", 82, 102, 1, GRIS, MC_DATUM);
  txtf(82, 116, 2, BLANCO, MC_DATUM, "%.1f", z.tObj);

  panel(162, 32, 154, 100, "HUMEDAD DEL SUELO", z.acento);
  uint16_t cs = d ? colRango(z.suelo, z.sMin, z.sMax) : GRIS;
  if (d) { char b[8]; snprintf(b, sizeof(b), "%.0f", z.suelo);
           txt(b, 170, 46, 4, cs); txt("%", 172 + 24 * strlen(b), 46, 2, cs); }
  else txt("--", 170, 46, 4, GRIS);
  barra(170, 88, 138, 7, d ? z.suelo : -99, 0, 100, z.sMin, z.sMax, cs);
  txtf(239, 102, 1, GRIS, MC_DATUM, "riega <%.0f%%  para >%.0f%%", z.sMin, z.sMax);
  const char* er = z.riego == 1 ? "REGANDO" : (z.riego == 2 ? "esperando que baje" : "en reposo");
  txt(er, 239, 118, 1, z.riego ? AZUL : GRIS, MC_DATUM);

  panel(4, 136, 312, 38, "AIRE HR", z.acento);
  uint16_t ch = d ? colRango(z.hr, z.hMin, z.hMax) : GRIS;
  if (d) txtf(12, 152, 2, ch, TL_DATUM, "%.0f%%", z.hr); else txt("--", 12, 152, 2, GRIS);
  barra(70, 157, 150, 7, d ? z.hr : -99, 0, 100, z.hMin, z.hMax, ch);
  txtf(310, 148, 1, GRIS, TR_DATUM, "ideal %.0f-%.0f%%", z.hMin, z.hMax);
  txtf(310, 162, 1, z.vent ? VERDE : GRIS, TR_DATUM, "vent %.0f%%", manual ? (z.vent ? 100.0f : 0.0f) : z.uVent);

  boton(B_MODO, "MODO", manual ? "MANUAL" : "AUTO", manual ? NARANJO : VERDE, NEGRO, true);
  boton(B_VENT,  "VENTILADOR", z.vent ? "ON" : "OFF", z.vent ? VERDE : GRIS, NEGRO, manual);
  boton(B_RIEGO, "RIEGO", z.riego == 1 ? "ON" : "OFF", z.riego == 1 ? AZUL : GRIS, NEGRO, manual);

  const char* ayuda = manual ? "MANUAL: toca VENTILADOR o RIEGO" : "Toca MODO para control manual";
  if (d && (z.alarmas & 1)) ayuda = "ALARMA RIEGO: revisar sonda o agua";
  else if (d && (z.alarmas & 2)) ayuda = "Sensor de suelo sin lectura";
  else if (d && (z.alarmas & 4)) ayuda = "Sensor DHT22 sin lectura";
  else if (!conectado()) ayuda = "Revisar cable G17->IO22 y GND";
  barraInferior(ayuda);
  if (millis() >= toastHasta && d && z.alarmas) { tft.fillRect(0, 214, 250, 26, NEGRO); txt(ayuda, 8, 227, 1, ROJO, ML_DATUM); }
}

void dibujar() {
  if (pantalla < 0) dibujarInicio(redibujarTodo);
  else dibujarDetalle(pantalla, redibujarTodo);
  redibujarTodo = false;
  hayDatosNuevos = false;
}

void alTocar(int x, int y) {
  ultimoToque = millis();
  if (pantalla < 0) {
    for (int i = 0; i < 3; i++)
      if (x >= cardX(i) && x < cardX(i) + CARD_W && y >= CARD_Y) { pantalla = i; redibujarTodo = true; }
    return;
  }
  DatosZona& z = zonas[pantalla];
  bool manual = z.estado == 2;
  char v[12];

  if (dentro(B_VOLVER, x, y)) { pantalla = -1; redibujarTodo = true; return; }

  if (dentro(B_MODO, x, y)) {
    enviar(z, "MODO", manual ? "AUTO" : "MANUAL");
    z.estado = manual ? 1 : 2;
    if (manual) { z.vent = 0; z.riego = 0; }
    toast(manual ? "Modo AUTO: el PI vuelve a controlar" : "Modo MANUAL: control desde la pantalla", NARANJO);
  } else if (dentro(B_VENT, x, y)) {
    if (!manual) { toast("Primero cambia MODO a MANUAL", AMARILLO); return; }
    z.vent = !z.vent;
    enviar(z, "VENT", z.vent ? "1" : "0");
    toast(z.vent ? "Ventilador ENCENDIDO" : "Ventilador APAGADO", z.vent ? VERDE : GRIS);
  } else if (dentro(B_RIEGO, x, y)) {
    if (!manual) { toast("Primero cambia MODO a MANUAL", AMARILLO); return; }
    bool on = z.riego != 1;
    z.riego = on ? 1 : 0;
    enviar(z, "BOMBA", on ? "1" : "0");
    toast(on ? "Riego ON (se apaga solo a los 30 s)" : "Riego OFF", AZUL);
  } else if (dentro(B_MENOS, x, y) || dentro(B_MAS, x, y)) {
    z.tObj = constrain(z.tObj + (dentro(B_MAS, x, y) ? 0.5f : -0.5f), 5.0f, 45.0f);
    snprintf(v, sizeof(v), "%.1f", z.tObj);
    enviar(z, "TOBJ", v);
    toast("Objetivo de temperatura enviado", BLANCO);
  } else return;
  hayDatosNuevos = true;
}

void revisarTactil() {
  static bool presionado = false;
  static uint32_t ultimo = 0;
  int rx, ry, z;
  bool toca = leerTactil(rx, ry, z);
  if (toca && !presionado && millis() - ultimo > 250) {
    delay(20);
    if (leerTactil(rx, ry, z)) {
      int x = constrain((int)map(rx, TS_MINX, TS_MAXX, 0, 319), 0, 319);
      int y = constrain((int)map(ry, TS_MINY, TS_MAXY, 0, 239), 0, 239);
      if (TACTIL_INV_X) x = 319 - x;
      if (TACTIL_INV_Y) y = 239 - y;
      Serial.printf("Toque: crudo %d,%d (presion %d) -> pantalla %d,%d\n", rx, ry, z, x, y);
      alTocar(x, y);
      ultimo = millis();
    }
  }
  presionado = toca;
}

void setup() {
  Serial.begin(115200);
  pinMode(CYD_BL, OUTPUT);
  digitalWrite(CYD_BL, HIGH);
  Serial2.begin(115200, SERIAL_8N1, RX_MAESTRO, TX_MAESTRO);

  tft.init();
  tft.setRotation(1);
  tft.invertDisplay(INVERTIR_COLORES);

  pinMode(T_CS, OUTPUT);   digitalWrite(T_CS, HIGH);
  pinMode(T_CLK, OUTPUT);  digitalWrite(T_CLK, LOW);
  pinMode(T_MOSI, OUTPUT); digitalWrite(T_MOSI, LOW);
  pinMode(T_MISO, INPUT);
  pinMode(T_IRQ, INPUT);
  Serial.println("Pantalla v3.1 lista. Toca la pantalla y mira aqui las coordenadas.");

  NEGRO    = TFT_BLACK;
  BLANCO   = TFT_WHITE;
  GRIS     = tft.color565(150, 150, 160);
  GRIS_OSC = tft.color565(55, 55, 65);
  MARCO    = tft.color565(70, 70, 85);
  VERDE    = tft.color565(40, 220, 100);
  AMARILLO = tft.color565(255, 205, 0);
  ROJO     = tft.color565(255, 60, 60);
  AZUL     = tft.color565(40, 150, 255);
  NARANJO  = tft.color565(255, 140, 0);
  zonas[0].acento = tft.color565(235, 150, 40);
  zonas[1].acento = tft.color565(120, 200, 60);
  zonas[2].acento = tft.color565(0, 190, 160);

  dibujar();
}

void loop() {
  leerSerie();
  revisarTactil();

  static uint32_t ultimoDibujo = 0;
  uint32_t ahora = millis();
  if (pantalla >= 0 && ahora - ultimoToque > VOLVER_INICIO_MS) { pantalla = -1; redibujarTodo = true; }
  if (toastHasta && ahora >= toastHasta) { toastHasta = 0; hayDatosNuevos = true; }
  if (redibujarTodo || hayDatosNuevos || ahora - ultimoDibujo > 3000) {
    dibujar();
    ultimoDibujo = ahora;
  }
}
