// ============================================================================
// BAJOTERRA - Prueba 04: relés (2 bombas y 2 ventiladores) en la ESP32 DevKit.
// Se maneja desde el Monitor Serie (115200 baudios), escribiendo una tecla y Enter:
//   1..4  -> enciende/apaga el relé 1..4
//   0     -> apaga todo
//   s     -> secuencia de prueba: cada relé 2 segundos, uno por uno
//
// SEGURIDAD:
//   - Al arrancar, todos los relés quedan APAGADOS.
//   - Las bombas se apagan solas a los 10 s (no se pueden dejar encendidas por olvido ni trabajar en seco mucho rato).
//   - Haz la primera prueba SIN cargas conectadas (solo escucha el "clic" y mira el LED de cada relé).
//   - Bombas y ventiladores se alimentan con una fuente de 5 V APARTE, nunca desde la ESP32 (ver docs/plan-hardware.md).
// ============================================================================

// El módulo de relés azul se activa con nivel BAJO (LOW = encendido). Si el tuyo es al revés, cambia a false.
const bool RELE_ACTIVO_BAJO = true;
// Tiempo máximo que una bomba puede estar encendida seguida (10 segundos).
const unsigned long BOMBA_MAX_MS = 10000;
// Duración de cada paso de la secuencia de prueba (2 segundos).
const unsigned long PASO_SECUENCIA_MS = 2000;

// Datos de un relé: nombre, GPIO, si es bomba (tiene límite de tiempo) y su estado actual.
struct Rele {
  // Nombre para mostrar.
  const char* nombre;
  // GPIO conectado a la entrada INx del módulo.
  int pin;
  // true si controla una bomba (se aplica el límite de tiempo).
  bool esBomba;
  // true si está encendido.
  bool encendido;
  // Momento (millis) en que se encendió.
  unsigned long desde;
};

// Asignación de docs/plan-hardware.md (cámbiala aquí si conectas distinto).
Rele RELES[] = {
  {"Rele 1 - Bomba 1 (zona humeda)",          25, true,  false, 0},
  {"Rele 2 - Bomba 2 (zona selvatica)",       26, true,  false, 0},
  {"Rele 3 - Ventilador 1 (zona arida)",      27, false, false, 0},
  {"Rele 4 - Ventilador 2 (zona selvatica)",  32, false, false, 0},
};
// Cantidad de relés.
const int N_RELES = sizeof(RELES) / sizeof(RELES[0]);

// Estado de la secuencia de prueba: -1 = inactiva; 0..N_RELES-1 = relé que está encendido ahora.
int pasoSecuencia = -1;
// Momento en que empezó el paso actual de la secuencia.
unsigned long inicioPaso = 0;

// Nivel eléctrico que corresponde a "encendido" o "apagado" según el tipo de módulo.
int nivel(bool encender) {
  // Activo en bajo: encendido = LOW; activo en alto: encendido = HIGH.
  return (encender != RELE_ACTIVO_BAJO) ? HIGH : LOW;
}

// Enciende o apaga un relé y lo informa.
void ponerRele(int i, bool encender) {
  // Escribe el nivel en el pin.
  digitalWrite(RELES[i].pin, nivel(encender));
  // Guarda el estado.
  RELES[i].encendido = encender;
  // Recuerda desde cuándo está encendido.
  RELES[i].desde = millis();
  // Informa.
  Serial.printf("%s -> %s\n", RELES[i].nombre, encender ? "ENCENDIDO" : "apagado");
}

// Apaga todos los relés.
void apagarTodo() {
  // Recorre los relés.
  for (int i = 0; i < N_RELES; i++) ponerRele(i, false);
}

// Muestra las instrucciones.
void mostrarMenu() {
  // Título.
  Serial.println("\n=== BAJOTERRA - Prueba 04: reles ===");
  // Opciones por relé.
  for (int i = 0; i < N_RELES; i++) Serial.printf("  %d -> %s (GPIO %d)\n", i + 1, RELES[i].nombre, RELES[i].pin);
  // Otras opciones.
  Serial.println("  0 -> apagar todo");
  Serial.println("  s -> secuencia de prueba (cada rele 2 s)");
}

// setup(): una vez al encender.
void setup() {
  // Monitor Serie.
  Serial.begin(115200);
  delay(300);
  // Configura cada pin como salida y lo deja APAGADO de inmediato.
  for (int i = 0; i < N_RELES; i++) {
    // Salida digital.
    pinMode(RELES[i].pin, OUTPUT);
    // Apagado (con módulo activo en bajo, esto es HIGH).
    digitalWrite(RELES[i].pin, nivel(false));
  }
  // Muestra el menú.
  mostrarMenu();
}

// loop(): se repite sin parar.
void loop() {
  // 1) Comandos desde el Monitor Serie.
  if (Serial.available()) {
    // Lee un carácter.
    char c = Serial.read();
    // Teclas 1..4: invertir el relé correspondiente.
    if (c >= '1' && c < '1' + N_RELES) {
      // Índice del relé.
      int i = c - '1';
      // Cancela la secuencia si estaba corriendo.
      pasoSecuencia = -1;
      // Invierte su estado.
      ponerRele(i, !RELES[i].encendido);
    // Tecla 0: apagar todo.
    } else if (c == '0') {
      // Cancela la secuencia y apaga.
      pasoSecuencia = -1;
      apagarTodo();
    // Tecla s: iniciar la secuencia de prueba.
    } else if (c == 's' || c == 'S') {
      // Parte con todo apagado.
      apagarTodo();
      // Primer paso: relé 0.
      pasoSecuencia = 0;
      inicioPaso = millis();
      ponerRele(0, true);
    // Ignora saltos de línea; cualquier otra tecla muestra el menú.
    } else if (c != '\n' && c != '\r') {
      mostrarMenu();
    }
  }
  // 2) Avance de la secuencia de prueba (sin bloquear).
  if (pasoSecuencia >= 0 && millis() - inicioPaso >= PASO_SECUENCIA_MS) {
    // Apaga el relé del paso actual.
    ponerRele(pasoSecuencia, false);
    // Pasa al siguiente.
    pasoSecuencia++;
    // ¿Quedan relés?
    if (pasoSecuencia < N_RELES) {
      // Enciende el siguiente.
      inicioPaso = millis();
      ponerRele(pasoSecuencia, true);
    } else {
      // Fin de la secuencia.
      pasoSecuencia = -1;
      Serial.println("Secuencia terminada.");
    }
  }
  // 3) Límite de seguridad de las bombas.
  for (int i = 0; i < N_RELES; i++) {
    // Bomba encendida por más del máximo permitido.
    if (RELES[i].esBomba && RELES[i].encendido && millis() - RELES[i].desde >= BOMBA_MAX_MS) {
      // Avisa y apaga.
      Serial.printf("SEGURIDAD: %s llevaba %lu s encendida; se apaga.\n", RELES[i].nombre, BOMBA_MAX_MS / 1000);
      ponerRele(i, false);
    }
  }
  // Pequeña pausa.
  delay(10);
}
