// ============================================================================
// BAJOTERRA - Controlador: configuración (pines, zonas y umbrales).
// Cambia aquí la repartición de sensores y actuadores; el programa principal no necesita cambios.
// ============================================================================

// Evita que este archivo se incluya dos veces.
#pragma once

// ---------------------------------------------------------------------------
// Modo de trabajo
// ---------------------------------------------------------------------------

// 1 = simulación en Wokwi (datos SIMULADOS, relés de Wokwi que se activan en HIGH).
// 0 = placa física (datos REALES, módulo de 4 relés que se activa en LOW).
// Si no se definió antes (por ejemplo en secretos.h), se usa 0 (placa física).
#ifndef MODO_WOKWI
// Valor por defecto: hardware real.
#define MODO_WOKWI 0
// Fin de la condición.
#endif

// ---------------------------------------------------------------------------
// Pines del ESP32 DevKit (ver docs/plan-hardware.md)
// ---------------------------------------------------------------------------

// Pin que alimenta (VCC) las 3 sondas de suelo: se enciende solo al medir para que no se corroan.
const int PIN_ALIM_SUELO = 33;
// Pin TX del UART hacia la pantalla CYD (Serial2).
const int PIN_UART_TX = 17;
// LED integrado: encendido fijo = WiFi conectado; parpadeo = sin WiFi.
const int PIN_LED_ESTADO = 2;

// Pines de los 4 relés: IN1, IN2, IN3, IN4.
const int PINES_RELE[4] = {25, 26, 27, 32};
// Nombres de lo que mueve cada relé (para el Monitor Serie).
const char* const NOMBRES_RELE[4] = {"Bomba 1", "Bomba 2", "Ventilador 1", "Ventilador 2"};
// Wokwi: relé activo en HIGH. Módulo físico: activo en LOW.
const bool RELE_ACTIVO_BAJO = (MODO_WOKWI == 0);

// ---------------------------------------------------------------------------
// Tiempos
// ---------------------------------------------------------------------------

// Cada cuánto se leen los sensores y se decide el control (el DHT22 necesita al menos 2 s).
const unsigned long INTERVALO_SENSORES_MS = 3000;
// Cada cuánto se envía una línea JSON a la pantalla CYD.
const unsigned long INTERVALO_PANTALLA_MS = 2000;
// Cada cuánto se envían las lecturas de las 3 zonas a Supabase.
const unsigned long INTERVALO_NUBE_MS = 15000;
// Cada cuánto se preguntan las órdenes pendientes de la web.
const unsigned long INTERVALO_ORDENES_MS = 5000;
// Tiempo máximo encendida de una bomba en una sola vez (seguridad: evita inundar).
const unsigned long BOMBA_MAX_MS = 20000;
// Descanso obligatorio de una bomba después de apagarse (deja que el agua llegue a la sonda).
const unsigned long BOMBA_DESCANSO_MS = 30000;
// Duración del modo manual tras una orden de la web; después vuelve el control automático.
const unsigned long MANUAL_MS = 120000;
// Tiempo máximo de cada petición HTTPS.
const uint16_t ESPERA_HTTP_MS = 10000;

// ---------------------------------------------------------------------------
// Zonas
// ---------------------------------------------------------------------------

// Descripción fija de una zona: pines, calibración, actuadores y umbrales.
struct ConfigZona {
  // Nombre usado en Supabase y en la web: "arida", "humeda" o "selvatica".
  const char* nombre;
  // Pin de datos del DHT22, o -1 si la zona no tiene DHT22.
  int pinDht;
  // Pin analógico (ADC1) de la sonda de suelo, o -1 si no tiene.
  int pinSuelo;
  // Valor crudo del ADC con la sonda SECA (en el aire).
  int crudoSeco;
  // Valor crudo del ADC con la sonda MOJADA (en un vaso con agua).
  int crudoMojado;
  // Índice del relé de la bomba (0..3), o -1 si la zona no tiene bomba.
  int releBomba;
  // Índice del relé del ventilador (0..3), o -1 si no tiene.
  int releVentilador;
  // Riego: la bomba se enciende cuando el suelo baja de este % ...
  float sueloEncender;
  // ... y se apaga al llegar a este % (histéresis).
  float sueloApagar;
  // Ventilación: se enciende si la temperatura supera este valor (°C) ...
  float temperaturaMax;
  // ... o si la humedad del aire supera este % .
  float humedadAireMax;
};

// Cantidad de zonas.
const int NUM_ZONAS = 3;

// Calibración de las sondas. En Wokwi un potenciómetro va de 0 a 4095; con la sonda real usa la prueba 03.
#if MODO_WOKWI
// Wokwi: potenciómetro a la derecha (4095) = seco; a la izquierda (0) = mojado.
#define SUELO_SECO 4095
// Valor "mojado" del potenciómetro.
#define SUELO_MOJADO 0
// Wokwi tiene un tercer DHT22 en el pin 13.
#define DHT_SELVATICA 13
// Placa física.
#else
// Valores de la sonda resistiva: AJÚSTALOS con la prueba 03 (modo calibración, tecla c).
#define SUELO_SECO 4095
// Valor en agua: 1480 es el que usaba el código antiguo del equipo con estas mismas sondas.
#define SUELO_MOJADO 1480
// Aún falta comprar el tercer DHT22: sin sensor (-1). Cámbialo a 13 cuando lo conectes.
#define DHT_SELVATICA -1
// Fin de la condición.
#endif

// Tabla de zonas. Los umbrales son valores de PRUEBA (no agronómicos): ajústalos con el cultivo real.
const ConfigZona ZONAS[NUM_ZONAS] = {
  // Árida: DHT22 en 4, suelo en 34, sin bomba (riego manual), Ventilador 1 (relé 2). Ventila si > 35 °C o > 40 % HR.
  {"arida", 4, 34, SUELO_SECO, SUELO_MOJADO, -1, 2, NAN, NAN, 35.0f, 40.0f},
  // Húmeda: DHT22 en 16, suelo en 35, Bomba 1 (relé 0), sin ventilador. Riega bajo 55 % hasta 70 %.
  {"humeda", 16, 35, SUELO_SECO, SUELO_MOJADO, 0, -1, 55.0f, 70.0f, 28.0f, 85.0f},
  // Selvática: DHT22 en 13 (o sin él), suelo en 36, Bomba 2 (relé 1), Ventilador 2 (relé 3). Riega bajo 60 % hasta 75 %.
  {"selvatica", DHT_SELVATICA, 36, SUELO_SECO, SUELO_MOJADO, 1, 3, 60.0f, 75.0f, 30.0f, 95.0f},
};

// Lecturas crudas fuera de [SUELO_CRUDO_MIN, SUELO_CRUDO_MAX] se toman como "sonda desconectada o fuera
// de la tierra" y NO se riega. Si tu tierra seca de verdad lee más de 4080, sube SUELO_CRUDO_MAX a 4094.
const int SUELO_CRUDO_MIN = 50;
// Máximo válido.
const int SUELO_CRUDO_MAX = 4080;

// Protección contra inundación: si después de regar el suelo no sube al menos MEJORA_MINIMA puntos,
// se cuenta un "ciclo sin mejora". Con MAX_CICLOS_SIN_MEJORA seguidos, la bomba se bloquea BLOQUEO_RIEGO_MS
// (por ejemplo: sonda fuera de la maceta, manguera suelta o depósito vacío).
const float MEJORA_MINIMA = 3.0f;
// Ciclos seguidos sin mejora antes de bloquear.
const int MAX_CICLOS_SIN_MEJORA = 3;
// Duración del bloqueo (1 hora). Reiniciar la placa también lo quita.
const unsigned long BLOQUEO_RIEGO_MS = 3600000UL;

// Histéresis del ventilador: se apaga cuando la temperatura baja 1 °C del máximo ...
const float HISTERESIS_TEMPERATURA = 1.0f;
// ... y la humedad del aire baja 3 puntos del máximo.
const float HISTERESIS_HUMEDAD = 3.0f;
