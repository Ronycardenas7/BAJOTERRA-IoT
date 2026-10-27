// Plantilla de credenciales de la Prueba 02. Copia este archivo como "secretos.h" y completa los datos.
// secretos.h está en .gitignore: NUNCA se sube a GitHub.

// Red WiFi de 2,4 GHz (en Wokwi usa "Wokwi-GUEST" y clave vacía "").
#define WIFI_SSID "nombre-de-tu-red"
#define WIFI_CLAVE "clave-de-tu-red"

// Proyecto de Supabase (Settings > API). La clave PUBLICABLE no es secreta, pero se deja aquí para tenerla junta.
#define SUPABASE_URL "https://tu-proyecto.supabase.co"
#define SUPABASE_PUBLISHABLE_KEY "sb_publishable_xxxxxxxxxxxxxxxx"

// Identidad del dispositivo: se crea en Supabase > SQL Editor con
//   select privado.crear_dispositivo('esp32-selvatica-01', 'zona', 'selvatica', 'ESP32 de prueba');
// La consulta devuelve la clave UNA sola vez: cópiala aquí.
#define DISPOSITIVO_ID "esp32-selvatica-01"
#define DISPOSITIVO_CLAVE "bjt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
