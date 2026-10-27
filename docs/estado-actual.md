# Estado actual

> **Actualización 2026-10-27 (madrugada):** pruebas "reales" en línea.
> - Migración 0004 (dispositivo `controlador`) **aplicada** en Supabase; creados `esp32-controlador-01` y `wokwi-controlador-01` (D-012).
> - Nuevo `firmware/controlador/` v1. **Compilado de verdad** con arduino-cli y el núcleo ESP32 3.0.7 (modo placa y modo Wokwi), igual que las pruebas 03, 04 y 05.
> - **Simulado en Wokwi** (navegador del PC del usuario): los 3 DHT22 y las 3 sondas (potenciómetros) se leen bien; la bomba 1 se encendió con suelo seco (30 %) y se apagó sola a los 20 s por seguridad; la selvática (70 %) quedó sin regar por la histéresis; WiFi `Wokwi-GUEST` y HTTPS hasta Supabase funcionan (respuesta 403 esperada porque la clave del dispositivo **no** se escribió en Wokwi: falta que el usuario la pegue).
> - Pendiente: pegar la clave en Wokwi y ver las lecturas `simulado` en la web; ejecutar `scripts\instalar_windows.bat` en el PC; probar en la placa real.

> **Actualización 2026-10-27 (noche):** plan de hardware real (D-011, `docs/plan-hardware.md`) y Pruebas 03 (sensores), 04 (relés) y 05 (pantalla CYD). Sintaxis revisada con g++ y cabeceras de imitación; **no compiladas ni probadas en las placas**. El repositorio se clonó en el PC "moniropc" (carpeta `ODIO ESTA CARRERA\Bajoterra`); allí no hay terminal remota disponible, así que las dependencias no se instalaron desde esta sesión.

> **Actualización 2026-10-27 (tarde):** datos en la nube con Supabase (Opción A, D-010). Ver la sección "Supabase y Prueba 02".

> **Actualización 2026-10-27:** se cambiaron las zonas a árida/húmeda/selvática y se rediseñó la web (ver D-009 y la sección "Cambio de zonas y rediseño" más abajo).

## Fecha y objetivo de la sesión

- **Fecha:** 2026-10-26
- **Objetivo:** dejar listo el proyecto para empezar (backend, simulador, web, broker, esquema SQL borrador) y **dockerizarlo**, siguiendo el stack de `AGENTS.md`.

## Archivos cambiados

Se crearon todos los archivos del repositorio (salvo `AGENTS.md`, que **no se modificó**). Ver la estructura en `README.md`.
Nada se confirmó (`git commit`) ni se subió a GitHub en esta sesión.

## Verificaciones realizadas (resultados reales, en un entorno de pruebas Linux sin Docker)

| Qué | Cómo | Resultado |
|---|---|---|
| Pruebas unitarias del backend | `pytest` | Pasaron |
| Pruebas unitarias del simulador | `pytest` | Pasaron |
| Flujo completo con un Mosquitto real: simulador → broker → backend → API | scripts de prueba contra Mosquitto con usuario y clave | Telemetría de 2 zonas y depósito recibida; comandos confirmados; duplicados y caducados ignorados |
| "Última voluntad" y parada ordenada del simulador | Matar el proceso y enviar SIGTERM | El estado `desconectado` se publica en ambos casos |
| Compilación de la web | `pnpm install --frozen-lockfile` y `pnpm build` (pnpm 10.28.0) | Compila |
| Web en navegador (escritorio y móvil) | Capturas con Chromium contra el backend real | Se muestra; se corrigió un error de formato de hora que dejaba la página en blanco |
| Esquema SQL | Ejecutado dos veces en PostgreSQL 16 local de pruebas | Idempotente; RLS activa; 3 inserciones inválidas rechazadas por las restricciones |
| nginx | Validación de sintaxis de la configuración | Correcta |

> Los números exactos de pruebas y las versiones usadas se pueden reproducir con los comandos del README. Vuelve a ejecutarlos en tu máquina.

### Modo sin Docker (agregado después, también en el entorno de pruebas Linux)

| Qué | Resultado |
|---|---|
| `pytest` del backend y del simulador con **Python 3.14.9** y las dependencias de `requirements-local.txt` | Pasaron |
| `python scripts/iniciar_local.py`: broker local + backend + simulador | `/salud` respondió `mqtt_conectado: true`; `/api/resumen` mostró telemetría simulada |
| Conexión con contraseña incorrecta al broker local | Rechazada ("Not authorized") |
| Orden de encendido de ventilador por la API | El simulador la ejecutó (visto en su registro) |
| Simulador terminado con `kill -9` | Las zonas pasaron a `desconectado` (última voluntad) |
| Parada ordenada con SIGTERM | No quedó ningún proceso vivo |
| Web con `corepack pnpm dev` (Vite) frente al backend sin Docker | El proxy `/api/resumen` devolvió los datos simulados |

### Cambio de zonas y rediseño de la web (2026-10-27, entorno de pruebas Linux)

| Qué | Resultado |
|---|---|
| `pytest` backend (47 pruebas, incluye CO₂, radiación y luces) y simulador (16 pruebas) con Python 3.14 | Pasaron |
| Simulación de 3 ciclos por zona | Valores plausibles; extractor y luces LED se activan según el perfil |
| Flujo completo con broker local: 3 zonas en `/api/resumen`, `co2`/`radiacion` como `null` donde no hay sensor | Correcto |
| `corepack pnpm build` | Compiló (JS 76,8 kB gzip, CSS 3,6 kB gzip) |
| Capturas con Chromium (escritorio 1366 px y móvil 390 px) de inicio y panel | Se ven bien; sin errores en consola |
| Botón "Encender Extractor" en la zona selvática desde la interfaz | La orden quedó "confirmado por sim-zona-selvatica (simulado)" |
| Enlace "Zonas" desde el panel hacia el ancla de la página de inicio | Funciona |
| SQL borrador con zonas/columnas nuevas en PostgreSQL 16 (2 ejecuciones) | Idempotente; rechazó zona "lechuga", CO₂ de 100 ppm y actuador "calefactor" |

### Corrección del panel, estructura y primera prueba del ESP32 (2026-10-27, tarde)

| Qué | Resultado |
|---|---|
| Error "Cannot read properties of undefined (reading 'lectura')" en el Panel | Reproducido simulando un backend antiguo (zonas lechuga/cactus). Causa: el backend en ejecución no se había reiniciado tras el cambio de zonas. La web ahora no se cae y muestra un aviso que pide reiniciar los servicios |
| Panel con backend nuevo después de la corrección | Orden "Encender Extractor" confirmada por el simulador |
| `firmware/prueba_01_wifi` (WiFi + NTP) | Sintaxis C++ revisada con g++ y cabeceras de imitación. **No compilado para ESP32** (sin acceso a las herramientas de Espressif en el entorno de desarrollo) y **no probado** en placa ni en Wokwi |
| `ESTRUCTURA.md` y `docs/tiempo-real.md` | Creados |

### Supabase, simulador nube, web nube y Prueba 02 (2026-10-27, tarde)

| Qué | Resultado |
|---|---|
| Proyecto Supabase `bajoterra-iot` (sa-east-1, plan gratuito) | Creado; migraciones 0001, 0002 y 0003 aplicadas con éxito |
| Migración 0002 en PostgreSQL 16 local (16 casos) | Clave falsa, medición desconocida, fuera de rango, texto en lugar de número, fecha sin zona, simulador declarando "real", ESP32 suplantando a otro, lectura sin sesión, orden sin ser operador y clave revocada: todos rechazados. Lectura válida, duplicada, orden de operador, pendientes por zona y confirmación: correctos |
| Nube: `registrar_lectura` con el rol `anon` (SQL, revertido) | `guardado` |
| Nube: 12 lecturas por HTTPS desde el navegador del PC del usuario | HTTP 200; guardadas con la hora corregida. La clave falsa da 403 y la lectura sin sesión 401 |
| Reloj del PC del usuario | Adelantado unos 54 min respecto del servidor; se agregó `hora_servidor()` y la corrección en el simulador y la web |
| `python -m sim.nube` contra PostgREST 12 local | Lecturas de 3 zonas + depósito y una orden de operador ejecutada y confirmada |
| `pytest` del simulador (20 pruebas, 4 nuevas del modo nube) | Pasaron |
| Web modo nube contra PostgREST local (sesión de prueba inyectada) | Pantalla de acceso, datos, insignia "Operador", orden confirmada. Con el reloj adelantado 54 min: muestra el aviso y las zonas siguen "En línea" |
| Firmware `prueba_02_supabase` | Sintaxis revisada con g++ y ArduinoJson 7.4.2 real; lógica ejecutada en PC con respuestas imitadas (ejecutado, rechazado, caducado, duplicado); su JSON fue aceptado por `registrar_lectura` local. **No compilado para ESP32** |

**Pendiente de verificar con el usuario:** inicio de sesión real (correo de confirmación), Realtime en la nube, simulador nube corriendo en su PC y la Prueba 02 en Wokwi o en la placa.

## NO verificado

- **Las imágenes Docker no se construyeron** y `docker compose up` **no se ejecutó**: el entorno de pruebas no tiene demonio de Docker. Los Dockerfile y el compose se revisaron y sus piezas se probaron por separado, pero el primer `docker compose up --build` en tu equipo es la prueba real.
- Los límites de memoria son estimados; no se midieron con `docker stats`.
- No se probó con hardware (ESP32, sensores, bombas). No se probó ESP-NOW.
- Supabase: se creó el proyecto nuevo `bajoterra-iot`; no se modificó ni se borró ningún otro recurso. GitHub: nada se subió.
- **El modo sin Docker no se ejecutó en Windows** (ni con `corepack pnpm`, ni `.venv\Scripts\python`). En Windows `terminate()` fuerza el cierre de los procesos.
- No se ejecutó en Windows (la carpeta de destino es una ruta de Windows). Los finales de línea de scripts/YAML se fijan a LF con `.gitattributes`.

## Decisiones nuevas y preguntas abiertas

- Ver `docs/decisiones.md` (D-001 a D-010).
- Docker se agregó por pedido explícito, aunque `AGENTS.md` dice "no introducir Docker por defecto". **`AGENTS.md` quedó sin cambios**: conviene actualizar esa línea para que no contradiga la decisión D-002.
- Abiertas: topología ESP-NOW, depósito compartido o por zona, proyecto de Supabase y autenticación, alcance exacto del "reinicio" de GitHub/Supabase.

## Próxima tarea y bloqueos

0. Ejecutar el simulador y la web en modo nube, crear la cuenta y darle permiso de operador; probar las Pruebas 01 y 02 en Wokwi o en la placa; publicar la web.
1. Ejecutar `docker compose up --build` en tu equipo y corregir lo que aparezca (anotarlo aquí).
2. Integrar Supabase: elegir proyecto, aplicar el esquema, implementar un repositorio de Supabase (la interfaz ya existe) y decidir autenticación/RLS.
3. Decidir topología ESP-NOW y del depósito antes de escribir el firmware.

Bloqueos: ninguno técnico. Faltan las decisiones indicadas arriba.

## Último commit

`17dead6` (el del clon inicial). Los cambios de esta sesión están sin confirmar en el árbol de trabajo.
