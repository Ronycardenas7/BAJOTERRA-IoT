// Plantilla de credenciales del controlador. Copia este archivo como "secretos.h" y completa los datos.
// secretos.h está en .gitignore: NUNCA se sube a GitHub.

// Descomenta la línea siguiente SOLO para la simulación en Wokwi (datos simulados, relés en HIGH).
// #define MODO_WOKWI 1

// Red WiFi de 2,4 GHz (en Wokwi usa "Wokwi-GUEST" y clave vacía "").
#define WIFI_SSID "nombre-de-tu-red"
// Clave del WiFi.
#define WIFI_CLAVE "clave-de-tu-red"

// Proyecto de Supabase. La clave PUBLICABLE no es secreta, pero se deja aquí para tenerla junta.
#define SUPABASE_URL "https://tu-proyecto.supabase.co"
// Clave publicable (sb_publishable_...).
#define SUPABASE_PUBLISHABLE_KEY "sb_publishable_xxxxxxxxxxxxxxxx"

// Identidad del dispositivo (tipo "controlador", migración 0004). Se crea en Supabase > SQL Editor con
//   select privado.crear_dispositivo('esp32-controlador-01', 'controlador', null, 'ESP32 DevKit controlador');
// La consulta devuelve la clave UNA sola vez: cópiala aquí.
#define DISPOSITIVO_ID "esp32-controlador-01"
// Clave secreta del dispositivo.
#define DISPOSITIVO_CLAVE "bjt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
