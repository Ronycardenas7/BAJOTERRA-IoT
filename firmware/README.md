# Firmware del ESP32

Código C++ (Arduino) de las placas ESP32. Se avanza con **pruebas pequeñas**, una por carpeta, antes de escribir el firmware final.

| Carpeta | Qué prueba | Estado |
|---|---|---|
| `prueba_01_wifi/` | Conexión WiFi, IP, señal y hora UTC por internet (NTP) | Escrita; **no compilada** en el entorno de desarrollo (sin acceso a las herramientas de Espressif). Compílala tú en Wokwi o Arduino IDE. |
| `prueba_02_supabase/` | Envía lecturas a Supabase por HTTPS cada 15 s y recibe órdenes cada 5 s (el LED integrado hace de "luces LED") | Escrita; sintaxis y lógica revisadas en PC; **no compilada** para ESP32 |

## Opción A: probar sin placa, en Wokwi (navegador, sin instalar nada)

1. Entra a <https://wokwi.com> y crea un proyecto nuevo **ESP32** (plantilla "ESP32").
2. En la pestaña `sketch.ino`, borra todo y pega el contenido de `prueba_01_wifi/prueba_01_wifi.ino`.
3. En la pestaña `diagram.json`, pega el contenido de `prueba_01_wifi/diagram.json`.
4. Pulsa el botón verde **▶ (Start the simulation)**.
5. En el Monitor Serie deberías ver algo así (los números cambian):

```
=== BAJOTERRA - Prueba 01: WiFi + hora UTC ===
[wifi] conectando a "Wokwi-GUEST"......
[wifi] conectado. IP: 10.10.0.2 | senal: -XX dBm (...) | MAC: ...
[hora] hora UTC sincronizada por NTP.
[estado] 2026-10-27T15:04:05Z | senal ... | memoria libre ... bytes
```

En Wokwi no hace falta `secretos.h`: sin ese archivo el programa usa la red simulada `Wokwi-GUEST`.

## Opción B: placa real con Arduino IDE

1. Instala **Arduino IDE 2** y, en *Herramientas → Placa → Gestor de tarjetas*, instala **esp32 by Espressif Systems**.
2. Abre `prueba_01_wifi/prueba_01_wifi.ino`.
3. Copia `secretos.ejemplo.h` como `secretos.h` en la misma carpeta y escribe el nombre y la clave de tu WiFi.
4. Elige la placa **ESP32 Dev Module** y el puerto COM de tu ESP32.
5. Pulsa **Subir** y abre el **Monitor Serie a 115200 baudios**.
6. Si al subir se queda en "Connecting....", mantén apretado el botón **BOOT** de la placa hasta que empiece a escribir.

### Importante sobre la red

- El ESP32 solo usa WiFi de **2,4 GHz**.
- Las redes de universidad con usuario y contraseña personal (por ejemplo **eduroam**, WPA2-Enterprise) **no funcionan** con este código sencillo. Usa la **zona WiFi de tu celular** u otra red con clave normal.
- El LED integrado (GPIO 2) parpadea mientras se conecta, queda **encendido** si hay WiFi y se **apaga** si se pierde.

## Prueba 02: lecturas y órdenes con Supabase

Necesita la biblioteca **ArduinoJson** (versión 7). En Arduino IDE: *Herramientas → Gestionar bibliotecas → "ArduinoJson" de Benoit Blanchon*. En Wokwi se instala sola gracias a `libraries.txt`.

1. Copia `prueba_02_supabase/secretos.ejemplo.h` como `secretos.h` y completa:
   - WiFi (en Wokwi: `Wokwi-GUEST` y clave vacía).
   - `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY`.
   - `DISPOSITIVO_ID` y `DISPOSITIVO_CLAVE`. La clave se crea en Supabase > SQL Editor con `select privado.crear_dispositivo('esp32-selvatica-01', 'zona', 'selvatica', 'ESP32 de prueba');`. Ojo: si lo vuelves a ejecutar, se genera una clave nueva y la anterior deja de servir.
2. **En Wokwi:** crea un proyecto ESP32 y pega `prueba_02_supabase.ino`, `diagram.json` y `libraries.txt`. Con el botón **+** agrega un archivo llamado `secretos.h` y pega tus datos. Luego pulsa ▶.
3. **En la placa:** abre el `.ino` en Arduino IDE y súbelo (placa *ESP32 Dev Module*).
4. En el Monitor Serie (115200) verás `[lectura] ... guardado` cada 15 s.
5. En el Panel de Control (modo nube, cuenta operador), pulsa **Encender Luces LED** en la **Zona Selvática**. En unos segundos el LED de la placa se enciende y el panel muestra la orden confirmada.

Los valores que envía esta prueba son **inventados** (no hay sensores): por eso van con origen `simulado`.
Bomba y extractor se responden como `rechazado` porque aún no están conectados.
