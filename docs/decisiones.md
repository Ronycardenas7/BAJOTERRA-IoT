# Decisiones de arquitectura

Registro de decisiones del proyecto. Cada una indica su estado: **acordada** (el usuario la confirmó) o **provisional** (supuesto para poder avanzar).

## D-001 — Stack: el del AGENTS.md (acordada, 2026-10-26)

- Backend y simulador en **Python** (Flask + paho-mqtt), web en **React + Vite (JavaScript)**, gestor de paquetes **pnpm**.
- Contexto: en una conversación previa se había propuesto Bun + TypeScript + Hono. Al revisar el repositorio se encontró que `AGENTS.md` fijaba pnpm y Python/Flask;
  se consultó al usuario y eligió el stack de `AGENTS.md`. La propuesta de Bun/Hono quedó descartada.

## D-002 — Docker: sí, por pedido explícito (acordada, 2026-10-26)

- `AGENTS.md` indicaba "no introducir Docker por defecto" por la poca RAM del equipo (3,3 GiB). El usuario pidió dockerizar el proyecto, y esa instrucción nueva prevalece.
- Para cuidar la memoria: imágenes base pequeñas (`python:3.12-slim`, `nginx:alpine`, `eclipse-mosquitto` sobre Alpine), un solo proceso por servicio y límites `mem_limit` por contenedor
  (mosquitto 64 MB, backend 192 MB, simulador 64 MB, web 32 MB: máximo 352 MB sumados).
  Estos límites son una estimación, **no una medición**: verificar con `docker stats`.
- La base de datos NO va en Docker: será Supabase (nube), para no gastar RAM local.

## D-003 — Broker: Mosquitto en Docker con usuario y contraseña (acordada, 2026-10-26)

- `AGENTS.md` dejaba el broker "por seleccionar". Se usa Mosquitto 2.0 por ser el más liviano y estándar.
- Sin acceso anónimo. El archivo de usuarios se genera al arrancar el contenedor desde `MQTT_USER` y `MQTT_PASSWORD` del `.env` (que no se sube a Git).
- El puerto MQTT se publica solo en `127.0.0.1`. Antes de usar un ESP32 real en la red local habrá que abrirlo con cuidado y agregar TLS y ACL.
- Sin persistencia: al reiniciar el broker no sobreviven mensajes `retained` viejos.

## D-004 — Almacenamiento en memoria hasta integrar Supabase (provisional)

- El backend guarda las últimas lecturas y comandos **en memoria** (se pierden al reiniciar) detrás de interfaces (`app/repositories/base.py`), para poder agregar una implementación de Supabase sin tocar los servicios.
- No se eligió proyecto de Supabase ni credenciales: `AGENTS.md` indica elegirlos "cuando esa integración corresponda". El usuario pidió reiniciar GitHub y Supabase, pero **ninguna eliminación está confirmada** y no se tocó nada remoto.
- `supabase/migrations/0001_esquema_inicial.sql` es un **borrador no aplicado**.

## D-005 — La web consulta por sondeo (polling) cada 3 s (provisional)

- Es lo más simple y no depende de Realtime, cuya autenticación y RLS siguen sin comprobarse. Se puede reemplazar por Supabase Realtime sin cambiar los componentes (solo el hook `useResumen`).

## D-006 — Depósito único `principal` (provisional)

- `AGENTS.md` deja abierto si el depósito es compartido o uno por zona. Se modeló un único depósito `principal` y una sola lectura de conductividad, **sin duplicarla** como si viniera de sensores independientes por zona.
- Un interruptor de nivel solo permite `agua_disponible`; `nivel_agua` queda en `null` salvo que exista un sensor de nivel.

## D-007 — Temas MQTT en español, según `AGENTS.md` (acordada)

- Se usó `bajoterra/01/zonas/{zona}/telemetria|comandos|confirmaciones`, `bajoterra/01/depositos/{deposito}/telemetria` y `bajoterra/01/dispositivos/{id}/estado`. Detalle en `docs/mqtt-topics.md`.

## D-008 — Modo sin Docker con broker en Python (acordada de palabra, 2026-10-26)

- El usuario no puede instalar Docker en el PC de la universidad (Windows con Python 3.14 y Node 24, sin permisos de instalación). Docker se mantiene como opción principal (D-002); se agrega un modo alternativo.
- El broker del modo sin Docker es `broker_local/broker.py` (librería `amqtt` 0.12.1, MQTT 3.1.1): usuario y contraseña obligatorios (clave guardada como hash Argon2 en una carpeta temporal fuera del repo) y solo escucha en `127.0.0.1`.
- Limitaciones: es para desarrollo; `amqtt` es mucho menos probado que Mosquitto y no se usará como broker definitivo. No tiene ACL por tema.
- Los archivos de Docker NO se borraron: no estorban y servirán en la máquina Linux Mint del usuario.

## D-009 — Zonas de evaluación: árida, húmeda y selvática (acordada, 2026-10-27)

- Reemplazan a lechuga y cactus en todo el sistema (backend, simulador, web, SQL borrador y documentación). Identificadores sin tildes: `arida`, `humeda`, `selvatica`.
- Nuevas mediciones opcionales por zona: `co2` (ppm, selvática) y `radiacion` (W/m², árida); donde no hay sensor se informa `null`, nunca 0. Nuevo actuador `luces` (LED). El actuador `ventilador` se muestra en la web como "Extractor".
- Los perfiles del simulador (temperatura, humedad, luz, CO₂, umbrales) son valores **inventados** para probar; no son parámetros agronómicos.
- La web mantiene **React + Vite** (se descartó reescribirla en JavaScript puro) sin librerías nuevas: los gráficos son SVG propios y la navegación usa el hash de la URL (`#/panel`), sin librería de rutas.
- El diseño (barra fija con vidrio, secciones, estilo oscuro) toma ideas del prototipo de Figma "GreenLab"; no se copiaron sus textos de especificaciones (por ejemplo precisión de sensores) porque no aplican a este proyecto.
- PWA: solo manifiesto e icono; **no hay service worker** todavía (evita mostrar datos viejos como si fueran actuales).

## D-010 — Datos en la nube: el ESP32 envía directo a Supabase por HTTPS (Opción A) (acordada, 2026-10-27)

- El usuario pidió elegir la opción más viable y empezar. Se eligió la **Opción A** de `docs/tiempo-real.md`: no necesita un PC encendido ni un servidor propio, HTTPS funciona en casi cualquier red y entra en el plan gratuito.
- **Cambia lo acordado en `AGENTS.md`:** en la nube el ESP32 ya no usa MQTT. El **formato JSON del mensaje se mantiene** (`docs/mqtt-topics.md`). MQTT con el backend Flask sigue disponible para trabajar en local. `AGENTS.md` no se modificó: el usuario debería actualizarlo.
- Proyecto Supabase **`bajoterra-iot`** creado en la organización "INVERNADERO" (región `sa-east-1`, plan gratuito). Migraciones 0001, 0002 y 0003 aplicadas.
- Seguridad: lectura solo con sesión (RLS); órdenes solo para `operadores`; escritura solo por funciones `SECURITY DEFINER` que exigen una clave de dispositivo, guardada como hash en el esquema `privado`. No se usa la clave secreta en ningún cliente.
- Estado de conexión en la nube: se deduce de la antigüedad de la última lectura (umbral de 60 s); no hay "última voluntad".
- Web: `@supabase/supabase-js` 2.117.3 (fijada; publicada hace más de 2 semanas). Modo nube por defecto, con la URL y la clave PUBLICABLE en `web_pwa/src/config/nube.js` (públicas por diseño). Modo local con `pnpm dev:local`, y Docker compila con `pnpm build:local`. No se usan archivos `.env` en la web porque las herramientas remotas no pueden escribirlos en el PC del usuario.
- Reloj: se agregó `hora_servidor()` (0003) porque un PC con la hora mal configurada fechaba mal las lecturas y la web veía todo como desactualizado.
- Limitación conocida: el firmware de la Prueba 02 no verifica el certificado TLS (`setInsecure`). Pendiente de corregir.

## D-011 — Hardware real: 2 ESP32 con cable, 3 zonas (acordada, 2026-10-27)

- Sin sensores inalámbricos (no se pueden conseguir). Todo va con cable.
- La "pantalla" ESP32-2432S028 es una **ESP32 con pantalla integrada (CYD)**. Arquitectura: la **DevKit** es el controlador (sensores, relés, nube) y la **CYD** es la pantalla, que recibe datos por **UART de un solo sentido** (DevKit GPIO 17 → CYD GPIO 22; antes se planeó el 35, ver D-013). La pantalla funciona sin internet.
- 3 zonas (árida, húmeda, selvática) con el inventario: 2 DHT22 (**falta 1 para la selvática**), 3 sondas de suelo resistivas, 2 bombas, 2 ventiladores y 4 relés. Asignación inicial: bomba 1 → húmeda, bomba 2 → selvática, ventilador 1 → árida, ventilador 2 → selvática. La árida queda con riego manual. Es configurable.
- No hay sensor de luz por zona; el LDR integrado de la CYD se usará como luz relativa (%) del invernadero, no en lux. CO₂ y radiación quedan `null` con hardware real.
- Sondas de suelo alimentadas desde un GPIO solo al medir (contra la corrosión). Bombas y ventiladores con fuente de 5 V aparte y GND común (contra los reinicios).
- Pantalla con la biblioteca Adafruit ILI9341 (en lugar de TFT_eSPI, que exige editar archivos de la biblioteca).
- Detalle completo: `docs/plan-hardware.md`.

## D-012 — Un dispositivo "controlador" para las 3 zonas (provisional, 2026-10-27)

- Migración `0004_dispositivo_controlador.sql` (**aplicada en Supabase** el 2026-10-27): nuevo tipo de dispositivo `controlador`. Una sola clave escribe en cualquier zona o depósito (el mensaje indica `"zona"`), ve las órdenes de todas las zonas y puede declarar origen `real`. Su campo `dispositivo` siempre es su propio id (no puede hacerse pasar por otro).
- Dispositivos creados: `esp32-controlador-01` (placa física) y `wokwi-controlador-01` (solo simulación; clave aparte para poder revocarla sin tocar la placa). Las claves están solo en archivos ignorados por Git en el PC del usuario.
- Motivo: sin sensores inalámbricos, una sola ESP32 con cable lee las 3 zonas (D-011); con 3 claves habría que fingir 3 dispositivos.
- Firmware `firmware/controlador/` v1: control local primero (funciona sin internet); en Wokwi los datos van como `simulado`.

## D-013 — Revisión del código antiguo del equipo (provisional, 2026-10-28)

El usuario entregó 4 archivos del prototipo anterior ("cerebro", "pantalla", "puente serial" y "base de datos"). Hallazgos y qué se usa:

- **Cerebro (ESP32):** leía 2 sondas de suelo (pines 34 y 32) y 2 LDR (35 y 33) y enviaba líneas con comas por Serial2 (TX 17). La temperatura era **fija en 25,0** (los DS18B20 se iniciaban pero no se leían) y los actuadores **nunca se encendían** (siempre `false`), con `delay(2000)` bloqueante. No era un control funcional.
  **Se adopta:** la calibración medida de las sondas (seco 4095, mojado **1480**) y el TX en GPIO 17 (ya era nuestro pin).
- **Pantalla (CYD):** TFT_eSPI, rotación horizontal, `invertDisplay(true)`, RX en **GPIO 22** y diseño con tarjetas grises, banner de color por cultivo y cambio automático cada 3 s.
  **Se adopta:** RX en GPIO 22 (antes planeábamos 35), `invertDisplay(true)` y el diseño (ahora para 3 zonas, en `firmware/pantalla/`).
  **No se adopta:** TFT_eSPI (exige editar `User_Setup.h` en cada PC; se siguen usando las bibliotecas de Adafruit) y el formato con comas (se usa el JSON del controlador). Detalle corregido: el código antiguo abría Serial2 con TX en GPIO 21, que es la luz de fondo; ahora TX = -1.
- **Puente serial (Python) + Flask/MySQL:** reemplazados por Supabase (D-010). Problemas encontrados: la expresión regular del puente esperaba un texto ("Enviado M1: ...") que el cerebro no imprimía, y **inventaba la luz** (550 y 850) como si fuera medición; MySQL con usuario root sin contraseña, clave secreta escrita en el código y `debug=True`.
  **Idea que se rescata (pendiente):** umbrales editables desde la web (tabla `configuracion`). Hoy los umbrales están fijos en `firmware/controlador/config.h`.

## D-014 — Protección contra inundación en el riego automático (provisional, 2026-10-28)

- Además del límite de 20 s por riego y 30 s de descanso, si 3 riegos automáticos seguidos no suben la humedad del suelo al menos 3 puntos, la bomba de esa zona se **bloquea 1 hora** y el Monitor Serie muestra `[ALERTA]`.
- Motivo: con la sonda fuera de la tierra, la manguera suelta o el depósito vacío, el control seguiría regando para siempre en ciclos de 20 s.
- Lecturas crudas fuera de 50–4080 se toman como "sonda desconectada" y no se riega (configurable en `config.h`). Falta mostrar el bloqueo en la web.

## Pendientes de decisión

- Comprar el 3er DHT22 (zona selvática). Confirmar si la CYD es ILI9341 o ST7789 (prueba 05).
- Confirmar si siguen disponibles los DS18B20 y las LDR del prototipo anterior.
- Umbrales editables desde la web (idea del código antiguo) y alerta de riego bloqueado en la web.
- Depósito compartido o por zona.
- Autenticación con Google (hoy: correo y contraseña) y dónde publicar la web (Vercel, Netlify o GitHub Pages).
- Qué hacer con el "reinicio" de GitHub y Supabase solicitado antes (identificar recursos exactos y respaldar primero).
