// ============================================================================
// BAJOTERRA - Prueba 03: sensores con cable en la ESP32 DevKit (controlador).
// Lee, para cada zona (árida, húmeda, selvática):
//   - DHT22: temperatura (°C) y humedad del aire (% HR).
//   - Sonda de humedad de suelo resistiva: valor crudo (0-4095) y % relativo según la calibración.
// Muestra todo en el Monitor Serie (115200 baudios). NO usa WiFi ni relés.
//
// Calibración del suelo (hacerla una vez por sonda):
//   1. Sonda al aire, seca: anota el valor "crudo" -> va en CRUDO_SECO.
//   2. Sonda metida en un vaso con agua (solo la parte metálica): anota el "crudo" -> va en CRUDO_MOJADO.
//   3. Copia los números en la tabla ZONAS de abajo y vuelve a subir el programa.
//
// Bibliotecas (Herramientas > Gestionar bibliotecas): "DHT sensor library" de Adafruit y "Adafruit Unified Sensor".
// Pines: ver docs/plan-hardware.md.
// ============================================================================

// Biblioteca del sensor DHT22 (Adafruit).
#include <DHT.h>

// ---------------------------------------------------------------------------
// Configuración
// ---------------------------------------------------------------------------

// Pin que alimenta (VCC) las tres sondas de suelo. Se enciende solo al medir para evitar la corrosión.
const int PIN_ALIM_SUELO = 33;
// Cada cuánto se muestra una ronda de lecturas (3 segundos; el DHT22 necesita al menos 2 s entre lecturas).
const unsigned long INTERVALO_MS = 3000;
// Cuántas muestras analógicas se promedian por sonda (reduce el ruido).
const int MUESTRAS_SUELO = 16;
// Milisegundos de espera tras encender las sondas antes de medir (para que el valor se estabilice).
const int ESPERA_ALIM_MS = 50;

// Datos de una zona: nombre, pin del DHT22 (-1 = no instalado), pin analógico de la sonda y su calibración.
struct Zona {
  // Nombre para mostrar.
  const char* nombre;
  // GPIO del pin de datos del DHT22, o -1 si la zona todavía no tiene DHT22.
  int pinDht;
  // GPIO analógico (ADC1) de la salida AO de la sonda de suelo.
  int pinSuelo;
  // Valor crudo con la sonda SECA (al aire). Valor provisional: reemplazar tras calibrar.
  int crudoSeco;
  // Valor crudo con la sonda en AGUA. Valor provisional: reemplazar tras calibrar.
  int crudoMojado;
};

// Tabla de zonas. La selvática no tiene DHT22 hasta comprar el tercero (pinDht = -1; cuando lo tengas, pon 13).
Zona ZONAS[] = {
  // nombre,      DHT, suelo, seco, mojado
  {"arida",        4,   34,   4095, 1500},
  {"humeda",      16,   35,   4095, 1500},
  {"selvatica",   -1,   36,   4095, 1500},
};
// Cantidad de zonas (calculada a partir de la tabla).
const int N_ZONAS = sizeof(ZONAS) / sizeof(ZONAS[0]);

// Un objeto DHT por zona (puntero nulo si la zona no tiene DHT22).
DHT* sensoresDht[N_ZONAS];

// true = mostrar solo los valores crudos de las sondas (útil al calibrar). Se cambia enviando "c" por el Monitor Serie.
bool modoCalibracion = false;
// Momento de la última ronda de lecturas.
unsigned long ultimaRonda = 0;

// ---------------------------------------------------------------------------
// Funciones
// ---------------------------------------------------------------------------

// Lee las tres sondas de suelo en una sola "encendida" y deja los valores crudos promediados en "crudos".
void leerSuelo(int crudos[]) {
  // Enciende la alimentación de las sondas.
  digitalWrite(PIN_ALIM_SUELO, HIGH);
  // Espera a que la lectura se estabilice.
  delay(ESPERA_ALIM_MS);
  // Recorre cada zona.
  for (int i = 0; i < N_ZONAS; i++) {
    // Acumulador de muestras.
    long suma = 0;
    // Toma varias muestras.
    for (int m = 0; m < MUESTRAS_SUELO; m++) {
      // Suma una lectura analógica (0 a 4095 con 12 bits).
      suma += analogRead(ZONAS[i].pinSuelo);
      // Pequeña pausa entre muestras.
      delay(2);
    }
    // Promedio.
    crudos[i] = suma / MUESTRAS_SUELO;
  }
  // Apaga la alimentación de las sondas (reduce la corrosión de las horquillas).
  digitalWrite(PIN_ALIM_SUELO, LOW);
}

// Convierte un valor crudo a % de humedad de suelo RELATIVO a la calibración (0 = seco, 100 = en agua).
// Las sondas resistivas dan un valor ALTO en seco y BAJO en agua.
float sueloAPorcentaje(const Zona& z, int crudo) {
  // Rango entre seco y mojado.
  int rango = z.crudoSeco - z.crudoMojado;
  // Si la calibración es inválida (rango nulo o invertido), no se inventa un valor: NAN = sin dato.
  if (rango <= 0) return NAN;
  // Regla de tres: cuánto se alejó del valor seco.
  float porcentaje = (z.crudoSeco - crudo) * 100.0 / rango;
  // Limita a 0..100 (pequeñas variaciones fuera de la calibración).
  return constrain(porcentaje, 0.0f, 100.0f);
}

// Interpreta un valor crudo: si está en los extremos, probablemente la sonda está desconectada o en cortocircuito.
const char* diagnosticoSuelo(int crudo) {
  // Prácticamente 0 V: cable de AO suelto con resistencia a GND, sonda en corto o placa sin alimentar.
  if (crudo < 50) return " (¿sonda en corto o sin alimentacion?)";
  // Prácticamente 3,3 V: sonda muy seca o desconectada.
  if (crudo > 4080) return " (¿sonda desconectada o totalmente seca?)";
  // Valor normal.
  return "";
}

// ---------------------------------------------------------------------------
// Programa principal
// ---------------------------------------------------------------------------

// setup(): una vez al encender.
void setup() {
  // Monitor Serie a 115200 baudios.
  Serial.begin(115200);
  // Pausa para que el monitor alcance a abrirse.
  delay(300);
  // Pin de alimentación de las sondas como salida, apagado.
  pinMode(PIN_ALIM_SUELO, OUTPUT);
  digitalWrite(PIN_ALIM_SUELO, LOW);
  // Resolución de 12 bits (0 a 4095) y rango hasta ~3,3 V en las entradas analógicas.
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  // Prepara los DHT22 que existan.
  for (int i = 0; i < N_ZONAS; i++) {
    // Sin DHT22 en esta zona: puntero nulo.
    if (ZONAS[i].pinDht < 0) {
      sensoresDht[i] = nullptr;
      continue;
    }
    // Crea el objeto para un DHT22 en ese pin.
    sensoresDht[i] = new DHT(ZONAS[i].pinDht, DHT22);
    // Lo inicia.
    sensoresDht[i]->begin();
  }
  // Mensaje de inicio con instrucciones.
  Serial.println("\n=== BAJOTERRA - Prueba 03: sensores ===");
  Serial.println("Envia 'c' en el Monitor Serie para activar/desactivar el modo calibracion (solo valores crudos).");
  // El DHT22 necesita unos 2 s tras encender para la primera lectura.
  delay(2000);
}

// loop(): se repite sin parar.
void loop() {
  // Revisa si llegó un comando por el Monitor Serie.
  if (Serial.available()) {
    // Lee un carácter.
    char c = Serial.read();
    // "c" o "C" cambia el modo calibración.
    if (c == 'c' || c == 'C') {
      // Invierte el modo.
      modoCalibracion = !modoCalibracion;
      // Informa el modo actual.
      Serial.println(modoCalibracion ? ">> Modo calibracion ACTIVADO" : ">> Modo calibracion DESACTIVADO");
    }
  }
  // Espera el intervalo sin bloquear (así se atienden los comandos).
  if (millis() - ultimaRonda < INTERVALO_MS) return;
  // Recuerda el momento de esta ronda.
  ultimaRonda = millis();
  // Lee las sondas de suelo.
  int crudos[N_ZONAS];
  leerSuelo(crudos);
  // Separador de ronda.
  Serial.println("------------------------------------------------------------");
  // Una línea por zona.
  for (int i = 0; i < N_ZONAS; i++) {
    // Modo calibración: solo el valor crudo, fácil de anotar.
    if (modoCalibracion) {
      Serial.printf("[%-9s] suelo crudo = %4d%s\n", ZONAS[i].nombre, crudos[i], diagnosticoSuelo(crudos[i]));
      continue;
    }
    // Temperatura y humedad del aire (NAN = sin dato).
    float temperatura = NAN;
    float humedadAire = NAN;
    // Solo si la zona tiene DHT22.
    if (sensoresDht[i] != nullptr) {
      // Lee la temperatura en °C.
      temperatura = sensoresDht[i]->readTemperature();
      // Lee la humedad relativa en %.
      humedadAire = sensoresDht[i]->readHumidity();
    }
    // Humedad del suelo en % relativo.
    float suelo = sueloAPorcentaje(ZONAS[i], crudos[i]);
    // Nombre de la zona.
    Serial.printf("[%-9s] ", ZONAS[i].nombre);
    // Aire: sin sensor, error de lectura o valores.
    if (sensoresDht[i] == nullptr) Serial.print("aire: SIN SENSOR (falta DHT22)       ");
    else if (isnan(temperatura) || isnan(humedadAire)) Serial.print("aire: ERROR DE LECTURA (revisa cables)");
    else Serial.printf("aire: %5.1f C  %5.1f %%HR            ", temperatura, humedadAire);
    // Suelo: porcentaje (o sin dato si la calibración es inválida) y valor crudo.
    if (isnan(suelo)) Serial.printf(" | suelo: sin dato (calibracion invalida), crudo %4d\n", crudos[i]);
    else Serial.printf(" | suelo: %5.1f %% (crudo %4d)%s\n", suelo, crudos[i], diagnosticoSuelo(crudos[i]));
  }
}
