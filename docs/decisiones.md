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

## Pendientes de decisión

- Topología ESP-NOW: nodos + gateway MQTT, o ESP32 directos al broker.
- Depósito compartido o por zona.
- Autenticación con Google (hoy: correo y contraseña) y dónde publicar la web (Vercel, Netlify o GitHub Pages).
- Qué hacer con el "reinicio" de GitHub y Supabase solicitado antes (identificar recursos exactos y respaldar primero).
