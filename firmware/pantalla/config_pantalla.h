// ============================================================================
// BAJOTERRA - Pantalla CYD: configuración.
// Cambia aquí el tipo de pantalla, los pines y los tiempos; el programa principal no necesita cambios.
// ============================================================================

// Evita que este archivo se incluya dos veces.
#pragma once

// ---------------------------------------------------------------------------
// Tipo de pantalla
// ---------------------------------------------------------------------------

// Hay dos versiones de la placa ESP32-2432S028:
//   - 1 puerto USB: controlador ILI9341.
//   - 2 puertos USB (micro-USB + USB-C): controlador ST7789.
// 0 = ILI9341 (biblioteca "Adafruit ILI9341"); 1 = ST7789 (biblioteca "Adafruit ST7735 and ST7789 Library").
// Si la pantalla queda en blanco o con basura, cambia este valor.
#define PANTALLA_ST7789 0

// Invertir colores. El código antiguo del equipo usaba invertDisplay(true) y se veía bien, así que se deja en 1.
// Si los colores se ven "en negativo" (fondo blanco en vez de negro), cámbialo a 0.
#define INVERTIR_COLORES 1

// ---------------------------------------------------------------------------
// Pines de la CYD (vienen fijos en la placa)
// ---------------------------------------------------------------------------

// Pantalla en el bus HSPI: reloj (SCK).
const int TFT_SCK = 14;
// Datos de la placa hacia la pantalla (MOSI).
const int TFT_MOSI = 13;
// Datos de la pantalla hacia la placa (MISO).
const int TFT_MISO = 12;
// Selección de la pantalla (CS).
const int TFT_CS = 15;
// Dato/comando (DC).
const int TFT_DC = 2;
// Luz de fondo (backlight).
const int TFT_LUZ_FONDO = 21;
// Sensor de luz (LDR) integrado en la placa.
const int PIN_LDR = 34;
// LED RGB integrado: rojo, verde y azul (se encienden en LOW).
const int LED_R = 4;
// Verde.
const int LED_G = 16;
// Azul.
const int LED_B = 17;

// ---------------------------------------------------------------------------
// Comunicación con el controlador (ESP32 DevKit)
// ---------------------------------------------------------------------------

// Pin RX del UART: GPIO 22, en el conector P3 o CN1 de la CYD. Es el mismo pin que usaba el código antiguo
// del equipo (que funcionaba). Se conecta al GPIO 17 (TX) de la DevKit, más un cable de GND común.
const int UART_RX = 22;
// Velocidad del UART (igual que en el controlador).
const long UART_BAUDIOS = 115200;

// ---------------------------------------------------------------------------
// Tiempos
// ---------------------------------------------------------------------------

// Cada cuánto cambia la zona mostrada (árida -> húmeda -> selvática).
const unsigned long CAMBIO_ZONA_MS = 4000;
// Cada cuánto se actualizan los números en pantalla.
const unsigned long REFRESCO_MS = 1000;
// Si no llega nada del controlador en este tiempo, los datos se marcan como DESACTUALIZADOS.
const unsigned long DATOS_VIEJOS_MS = 10000;
