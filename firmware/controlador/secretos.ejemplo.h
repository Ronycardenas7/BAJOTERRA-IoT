// ============================================================================
// BAJOTERRA - Plantilla de credenciales privadas del Maestro ESP32 (v3.0).
// Copia este archivo como "secretos.h" y completa con tus datos reales.
// "secretos.h" está en .gitignore y NUNCA se sube a GitHub.
// ============================================================================
#pragma once

// Credenciales de la red Wi-Fi (debe ser red de 2,4 GHz).
#define WIFI_SSID_VAL "nombre-de-tu-red-2.4G"
#define WIFI_PASS_VAL "clave-de-tu-red"

// Dirección del proyecto en Supabase (sin barra '/' al final).
#define SUPABASE_URL_VAL "https://tu-proyecto.supabase.co"

// Clave publicable anon de Supabase (la misma de web_pwa/src/config/nube.js).
#define SUPABASE_KEY_VAL "sb_publishable_tu_clave_publicable"

// Identificador del dispositivo en la tabla dispositivos de Supabase.
#define DISPOSITIVO_ID_VAL "esp32-controlador-01"

// Clave secreta del dispositivo controlador (generada con privado.crear_dispositivo).
#define CLAVE_DISPOSITIVO_VAL "bjt_tu_clave_secreta_aqui"
