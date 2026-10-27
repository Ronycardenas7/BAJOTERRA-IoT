# Firmware del ESP32

Código C++ (Arduino) de las placas ESP32. Se avanza con **pruebas pequeñas**, una por carpeta, antes de escribir el firmware final.

| Carpeta | Qué prueba | Estado |
|---|---|---|
| `controlador/` | **Firmware principal de la DevKit (v1)**: 3 zonas, riego y ventilación automáticos, UART a la CYD, lecturas a Supabase y órdenes de la web | **Compilado** (núcleo ESP32 3.0.7) y **probado en Wokwi** (control local); falta la nube con clave y la placa real |
| `prueba_01_wifi/` | Conexión WiFi, IP, señal y hora UTC por internet (NTP) | Escrita; no compilada en el entorno de desarrollo. Compílala tú en Wokwi o Arduino IDE. |
| `prueba_03_sensores/` | **DevKit**: DHT22 y 3 sondas de suelo (con calibración seco/agua) en el Monitor Serie | **Compilada** (núcleo ESP32 3.0.7); falta probar en la placa |
| `prueba_04_reles/` | **DevKit**: relés de 2 bombas y 2 ventiladores, menú por Monitor Serie, bombas con límite de 10 s | **Compilada** (núcleo ESP32 3.0.7); falta probar en la placa |
| `prueba_05_pantalla_cyd/` | **CYD (ESP32-2432S028)**: pantalla con las 3 zonas (valores de ejemplo), LDR integrado y recepción UART en GPIO 35 | **Compilada** (núcleo ESP32 3.0.7); falta probar en la placa |
| `prueba_02_supabase/` | Envía lecturas a Supabase por HTTPS cada 15 s y recibe órdenes cada 5 s (el LED integrado hace de "luces LED") | Escrita; sintaxis y lógica revisadas en PC; **no compilada** para ESP32 |

## Controlador v1 (`controlador/`)

Un solo programa para la ESP32 DevKit que maneja las 3 zonas. Archivos:

| Archivo | Para qué |
|---|---|
| `controlador.ino` | Programa principal (en Wokwi se pega en `sketch.ino`) |
| `config.h` | Pines, zonas, umbrales y tiempos. **Lo que más vas a ajustar** |
| `secretos.ejemplo.h` | Plantilla de `secretos.h` (WiFi, Supabase y clave del dispositivo). `secretos.h` no se sube a Git |
| `diagram.json`, `libraries.txt` | Circuito y bibliotecas para Wokwi |

**Reglas de control (valores de prueba, no agronómicos):** húmeda riega bajo 55 % hasta 70 %; selvática riega bajo 60 % hasta 75 %; la árida no tiene bomba. Ventilador 1 (árida) sobre 35 °C o 40 % HR; ventilador 2 (selvática) sobre 30 °C o 95 % HR.
**Seguridad:** una bomba nunca pasa de 20 s seguidos y luego descansa 30 s; sin dato de suelo **no riega**; una orden de la web deja ese actuador en manual 2 min.

### En Wokwi (simulación)

1. Proyecto nuevo ESP32 en <https://wokwi.com>. Pestañas: `sketch.ino` (pega `controlador.ino`), `diagram.json`, y crea `config.h` y `secretos.h` (botón ▾ → *New file*).
2. En `secretos.h` pon `#define MODO_WOKWI 1`, WiFi `Wokwi-GUEST` con clave `""` y el dispositivo `wokwi-controlador-01` con su clave (está en `clave_wokwi.txt`, que no se sube a Git).
3. *Library Manager* → agrega **DHT sensor library**, **Adafruit Unified Sensor** y **ArduinoJson**.
4. ▶. Mueve los potenciómetros (suelo) y haz clic en los DHT22 para cambiar temperatura y humedad. Los LED azules son las bombas y los celestes los ventiladores.
5. **No guardes el proyecto con la clave puesta** (los proyectos guardados de Wokwi pueden ser públicos). Si se filtra, se revoca en Supabase.

### En la placa física

1. Copia `secretos.ejemplo.h` como `secretos.h` (o usa el que ya está en tu PC) y escribe tu WiFi de 2,4 GHz. **No** definas `MODO_WOKWI`.
2. Calibra las sondas con la prueba 03 y pon los valores en `config.h` (`SUELO_SECO`, `SUELO_MOJADO`).
3. Placa **ESP32 Dev Module**, sube el programa y abre el Monitor Serie a 115200.

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

## Pruebas 03, 04 y 05 (hardware real)

Antes de conectar nada, lee **`docs/plan-hardware.md`**: tiene la tabla de pines, la alimentación (bombas con fuente aparte) y el orden de las fases.

- **Prueba 03 (DevKit):** conecta los DHT22 y las sondas (VCC de las sondas al GPIO 33, **no** a 5 V) y sube el programa.
  - En el Monitor Serie (115200) verás cada zona cada 3 s.
  - Envía `c` para ver solo los valores crudos y **calibrar** cada sonda: primero seca, al aire; luego con la parte metálica en un vaso con agua. Anota los dos números en la tabla `ZONAS` del código.
- **Prueba 04 (DevKit):** primero **sin cargas** (solo el "clic" de cada relé).
  - Teclas `1`–`4` encienden o apagan cada relé, `0` apaga todo y `s` hace una secuencia.
  - Luego conecta los ventiladores y, por último, las bombas, con su fuente de 5 V aparte y la manguera en agua.
- **Prueba 05 (CYD):** conecta la CYD por USB, elige la placa *ESP32 Dev Module* y sube el programa. Debe verse la pantalla de BAJOTERRA con las 3 zonas.
  - Si queda en blanco, avisa: puede ser la versión con controlador ST7789.
