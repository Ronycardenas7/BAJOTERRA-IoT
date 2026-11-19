# Estado actual

## Revisión de Wi-Fi y HTTPS del Maestro - 2026-11-19

- Se revisaron maestro.ino y nodo.ino. El Maestro reintenta la misma red cada dos minutos tras un intento fallido y sube lecturas actuales sin cola histórica. Los nodos buscan un SSID fijo para localizar el canal ESP-NOW. El cliente TLS tiene desactivada la validación del certificado.
- Solo se actualizó esta nota. Sin pruebas de hardware ni cambios de firmware. Para una red nueva, comprobar el canal y la recepción de las tres zonas. Último commit de referencia: 8e15658.

## Control de riego automático en el panel — 2026-11-19

- Las tres zonas muestran una fila «Riego automático». Encender envía el modo automático y apagar pasa a manual. El Maestro actual comparte ese modo con el extractor. La bomba conserva su control manual propio.
- Compilación correcta. Chromium verificó ambos cambios con confirmaciones simuladas. Último commit de referencia: `8e15658`. Pendiente verificar desde el frontend publicado con el equipo en línea.

## Alineación de tarjetas del panel — 2026-11-19

- Las zonas de una misma fila tienen igual ancho y altura. Comparten las posiciones de cabeceras, métricas y actuadores en escritorio, y se apilan en móvil. Verificado con Chromium y compilación de producción. Último commit de referencia: `8e15658`.

## Navegación con sesión activa — 2026-11-19

- La aplicación comprueba la sesión antes de mostrar la portada. Durante una sesión activa, los enlaces públicos se ocultan y cualquier intento de abrir el inicio vuelve al panel. «Cerrar sesión» está en la barra superior y devuelve al inicio cuando termina la sesión del navegador.
- Compilación correcta. En Chromium se probaron Atrás, dirección manual, entrada directa, cierre y recuperación con Supabase simulado. Último commit de referencia: `8e15658`. Cambio local pendiente de publicar.

## Revisión previa al despliegue en Vercel — 2026-11-19

- Se revisaron `web_pwa/package.json`, el lockfile, `web_pwa/vercel.json` y las redirecciones de Supabase Auth. El frontend ya contiene la URL y la clave publicable de Supabase.
- La compilación de Vite con las dependencias locales y Node 26.13.1 generó `web_pwa/dist/`. Corepack no estaba disponible en la terminal de esta revisión, así que no se repitió la instalación limpia.
- Rama `cambio-de-frontend`, último commit `8e15658`, con cambios locales pendientes. No se publicó. Siguiente paso: subir los cambios revisados a la rama, comprobar el Preview y verificar los correos de Auth con el dominio publicado.

## Cambio de modo manual y automático — 2026-11-19

- Se corrigió y aplicó `0005_ampliar_comandos_y_maestro_v3.sql` en Supabase. El RPC de órdenes acepta los dos modos y el Maestro v3 consulta y confirma por sus propias firmas HTTP, que delegan en la autenticación existente.
- En Chromium se probaron ambos botones con confirmaciones simuladas; el panel muestra el último modo confirmado hasta que llega la telemetría. En Supabase se probaron ambas órdenes, su confirmación y el modo de la lectura en una transacción revertida. La API HTTP rechazó claves de dispositivo inválidas.
- Compilación correcta. La base de datos no tenía lecturas reales recientes al verificar. Pendientes: publicar el frontend y probar ambos cambios con el Maestro en línea. Último commit de referencia: `8e15658`.

## Acceso, recuperación y permiso de control — 2026-11-19

- Se rediseñó el acceso con el fondo de la portada y se añadió la recuperación por enlace de Supabase Auth. El panel incluye las últimas 12 órdenes de los controles disponibles con estado y hora de Santiago.
- Se aplicó `0006_operadores_cuentas_confirmadas.sql` en Supabase. Las tres cuentas confirmadas existentes obtuvieron el permiso y las futuras se agregan al confirmar el correo. Una transacción luego revertida verificó que la cuenta de prueba no tuviera permiso antes de confirmar y que luego pudiera invocar el RPC de órdenes.
- Compilación correcta. Chromium comprobó acceso, registro, recuperación, enlace vencido, cambio de contraseña y el historial con Supabase simulado. Pendientes de esa revisión: desplegar el frontend, verificar SMTP y la URL de redirección con un correo real y validar órdenes con hardware. Último commit de referencia: `8e15658`.

## Fondo fotográfico de la portada — 2026-11-19

- Se retiró la foto del montaje de la portada. La sección muestra el texto sobre el fondo fotográfico. La compilación y la prueba en Chromium móvil y escritorio pasaron.

- El fondo actual es una [fotografía de Brands&People](https://unsplash.com/photos/a-greenhouse-with-a-dirt-path-between-rows-of-plants-OZyfbklpVwM) con cultivos verdes y un camino de tierra. Se optimizó en WebP para móvil (94 kB) y escritorio (271 kB).

- Se retiró el botón «Abrir Panel en Vivo» que estaba debajo del texto de portada. El acceso de la barra superior sigue disponible. La compilación pasó.
- Se retiraron también los cuatro enlaces de las tarjetas de ecosistemas y el botón «Explorar Panel Completo». La compilación pasó.

- La portada usa como fondo una [fotografía de Adrien Olichon](https://unsplash.com/photos/a-long-walkway-inside-a-greenhouse-filled-with-plants-xGQET8KLrEg), publicada bajo la licencia de Unsplash. Se guardaron dos tamaños en WebP. La fotografía del montaje de BAJOTERRA se sigue mostrando en su propio marco.
- Compilación correcta con Corepack. En Chromium se comprobaron la carga de las imágenes en móvil y escritorio, las capas de los dos temas y la navegación al panel. Último commit de referencia: `8e15658`. Cambio local pendiente de publicar.

## Iconos de magnitudes ambientales — 2026-11-19

- Se integraron seis SVG locales de Tabler Icons con su licencia MIT en `web_pwa/public/assets/iconos/tabler/`. Los aros usan acentos adaptados a los temas claro y oscuro.
- Compilación correcta con Corepack. En Chromium se comprobó la carga de los seis SVG, ambos temas y el ancho de 320 px. Último commit de referencia: `8e15658`. Cambio local pendiente de publicar.

## Carrusel continuo de hardware — 2026-11-19

- La galería ahora usa una sola lista con siete fichas. Maestro y nodos comparten la ficha ESP32. El desplazamiento automático vuelve al inicio al terminar la lista. Compilación y verificación en Chromium correctas.

- Las ocho fichas de la sección de hardware corresponden al firmware activo: Maestro, nodos, CYD, DHT22, sonda FC-28, relés, bombas y extractores. Las ilustraciones disponibles se reutilizan y los dos tipos de motores tienen sus propios iconos.
- El carrusel avanza en vertical al entrar en pantalla, vuelve al inicio sin salto visual y admite pausa y recorrido manual. Con movimiento reducido arranca en modo manual.
- Verificado con `corepack pnpm build` y Chromium en escritorio y móvil. Se probaron el cierre del ciclo, la pausa, el teclado y el gesto táctil. Último commit de referencia: `8e15658`. Cambio local pendiente de publicar.

## Carrusel de microclimas y temas — 2026-11-19

- El carrusel de fotos ahora avanza en horizontal a velocidad constante y se repite. Conserva los controles manuales sin añadir un botón de pausa. El avance se suspende al pasar el ratón o mientras se elige una foto, y queda desactivado con movimiento reducido. Compilación y pruebas en Chromium de escritorio y móvil correctas.

- La sección «Más que un simple invernadero» muestra las fotos individuales de Árida, Húmeda y Selvática en un carrusel con desplazamiento táctil, flechas, teclado e indicadores. Anime.js anima la descripción al pasar el ratón. Los efectos respetan la preferencia de movimiento reducido.
- La portada y el panel comparten el selector de tema claro y oscuro. El panel conserva la rejilla de zonas, depósito y controles de la referencia publicada en `PruebaOnline`. El retorno de confirmación de Supabase ahora restaura la sesión antes de abrir `#/panel`.
- Verificado con `corepack pnpm build` y Chromium. Se probaron cinco anchos, el gesto táctil, la persistencia del tema y el acceso con Supabase simulado, incluyendo enlaces de confirmación válidos y vencidos. Último commit de referencia: `8e15658`. Pendiente probar la autenticación con el dominio y los correos reales.

## Auditoría del frontend y fotografías — 2026-11-19

- Se integraron cuatro fotos del montaje en `web_pwa/public/assets/fotos/` (466 kB en WebP). La foto general se comparte entre la portada y la sección del proyecto. Las tres fotos restantes corresponden a Árida, Húmeda y Selvática.
- Se corrigieron referencias a imágenes inexistentes, navegación móvil, la rejilla de magnitudes y estilos perdidos del acceso y del panel. La portada ya no anuncia estados operativos fijos ni presenta como instalados los sensores ausentes.
- Se reforzaron la sesión, las lecturas que llegan fuera de orden y el seguimiento de comandos. La compilación con Corepack pasó. En Chromium se verificaron cinco anchos de pantalla y, con Supabase simulado, inicio y cierre de sesión, permisos, lecturas, eventos Realtime y confirmación de órdenes.
- Último commit de referencia: `8e15658`. La prueba del dominio de Vercel, la sesión real y el recorrido con el ESP32 quedan pendientes.

## Revisión de contexto — 2026-11-19

- Se revisaron los Markdown de la raíz y de `docs/`, junto con los dos textos de referencia de la portada. Los adjuntos quedan como contexto para una futura solicitud de diseño.
- En la rama `cambio-de-frontend`, `maestro.ino` confirma ESP-NOW, seis relés, UART bidireccional, subida HTTPS cada 30 s y consulta de órdenes cada 5 s. El plan de hardware, la guía de armado y el prompt de Antigravity aún describen en parte el prototipo cableado anterior.
- Revisión documental y estática, sin cambios de código ni pruebas en hardware, Supabase o Vercel. Último commit de referencia: `8e15658`. Sigue pendiente verificar la migración 0005 en la nube y el recorrido de telemetría y órdenes con hardware real.

## Limpieza para Vercel — 2026-11-19

- Retirados Docker, Flask, los brokers MQTT, el simulador de software y los scripts de arranque local. El panel obtiene lecturas, sesión y órdenes directamente de Supabase.
- El README y el mapa del repositorio describen el flujo ESP32 → Supabase → web y el despliegue desde `web_pwa/`. El firmware y las migraciones se conservan.
- La instalación con lockfile congelado y la compilación con Corepack y pnpm 10.28.0 pasaron. Último commit de referencia: `8e15658`. Pendiente la validación con el dominio de Vercel y una sesión real.

## Ajuste del panel y preparación para Vercel — 2026-11-19

- En la rama `cambio-de-frontend`, se retiró el actuador de iluminación de la interfaz de las tres zonas y del adaptador de telemetría. El depósito muestra sus propias mediciones y las tarjetas toleran datos ausentes.
- `web_pwa/vercel.json` entrega `index.html` como respaldo de la SPA. Vite minifica con esbuild y omite los mapas de código fuente. El panel se carga bajo demanda desde la ruta existente `/#/panel`.
- `corepack pnpm build` pasó con pnpm 10.28.0 y Vite 8.3.5, sin advertencias de compilación. Se verificaron el JSON, el chunk del panel, la ausencia de mapas y el manejo de valores antiguos y ausentes con filas de prueba.
- Último commit al verificar: `8e15658`. Queda por comprobar la recarga en un despliegue de Vercel y la telemetría en vivo.

## Revisión de GitHub — 2026-11-19

- Objetivo: contrastar el contexto entregado con `PruebaOnline`, `main` y los archivos locales.
- GitHub confirmó `PruebaOnline` en `dbc173191aa2463d068085c51ca3eee3677a22d3`, igual al commit local y cuatro commits por delante de `main` (`538dd41`). La portada rediseñada tiene cambios locales pendientes. Esta revisión solo actualizó este registro.
- El árbol publicado contiene nodos ESP-NOW, Maestro de seis relés y pantalla CYD táctil con UART bidireccional. El Maestro configura telemetría cada 30 s y consulta de órdenes cada 5 s. La migración 0005 está versionada. Flask, MQTT, Docker y simulador siguen en el repositorio como modo local.
- Verificación documental y estática con GitHub y Git. La consulta de estados del commit no devolvió comprobaciones. En esta revisión no se compiló ni se probó hardware, ni se verificó la aplicación de 0005 en Supabase o un despliegue en Vercel. La compilación que figura más abajo pertenece al registro anterior del rediseño.
- Próxima comprobación técnica: confirmar la migración 0005 en la nube y probar el recorrido nodo → Maestro → Supabase → panel con una orden confirmada. Antes de usar el sistema en producción, revisar `tls.setInsecure()` en el Maestro, que desactiva la validación del certificado HTTPS.

> **Actualización 2026-11-19:** Rediseño editorial verde bosque profundo + verde lima vibrante (`web_pwa/`, rama `PruebaOnline`).
> - **Paleta cromática exacta:** Fondo verde bosque oscuro (`#0A1911` a `#0F2418`), superficies en verde musgo (`#122B1D`), acentos CTA en verde lima vibrante (`#B6E33D` / `#C4F042`) y tipografía blanca pura (`#FFFFFF`) con verde salvia claro (`#A7C4B5`).
> - **Header minimalista (`Encabezado.jsx`):** Isotipo circular de invernadero/hoja, marca BAJOTERRA, enlaces separados por `|` (`Inicio | Zonas | Arquitectura | Hardware`), indicador `Invernadero IoT v3.0 · Tarapacá` y botón contorno lima `Ir al Panel`.
> - **Hero asimétrico de 2 columnas (`Hero.jsx`):** Título de 3 líneas ("Invernadero inteligente con control microclimático autónomo"), subtítulo breve, botón lima `Abrir Panel en Vivo` y fotografía enmarcada (24px) del invernadero real de 3 módulos (`invernadero-real.jpg`).
> - **Fila de 4 tarjetas simétricas (`Zonas.jsx` / `ZonaCard.jsx`):** Zona Árida (*Cactus*), Zona Húmeda (*Oreja de Oso y Tagete*), Zona Selvática (*Schefflera*) y Depósito Central (*Sistema Hídrico*), con imagen superior, 3 viñetas, doble píldora (estado en lima y botón `Ver zona`), y botón centrado `Explorar Panel Completo`.
> - **Editorial "Más que un simple invernadero" + 5 métricas (`Proyecto.jsx`):** Párrafos de autonomía ESP-NOW/Supabase, fotografía circular 50% con resplandor lima y fila de 5 indicadores destacados (`3`, `4`, `24/7`, `2.4 GHz`, `100%`).
> - **Galería de Hardware del Sistema (`ComponentCarousel.jsx`):** Columna fija izquierda con título/contexto + 3 tarjetas horizontales para ESP32 Maestro & Nodos, Pantalla CYD y Sensores & Relés.
> - **Variables monitoreadas conectadas (`Variables.jsx`):** 6 círculos simétricos con aro lima y números de paso para Temperatura, Humedad del Aire, Humedad del Sustrato, CO₂, Radiación Solar y Conductividad.
> - **Compilación web comprobada:** `pnpm run build` en `web_pwa` completado con éxito (0 errores) en 299 ms.

> **Actualización 2026-10-28:** revisión del código antiguo del equipo y preparación del armado físico (PC de la universidad "tecnologia-11", rama `PruebaOnline`).
> - Revisados los 4 códigos antiguos (cerebro, pantalla, puente serial, Flask/MySQL): qué se adopta y qué no en **D-013**.
> - Nuevo **`firmware/pantalla/`** (programa final de la CYD): recibe el JSON del controlador por GPIO 22, muestra las 3 zonas rotando y avisa si los datos están viejos. **Compilado** con ILI9341 y con ST7789 (sin advertencias). No probado en la placa ni en Wokwi (Wokwi pidió iniciar sesión en este PC).
> - Controlador: protección contra inundación (**D-014**), calibración por defecto `SUELO_MOJADO 1480` (del código antiguo) y límites crudos configurables. **Recompilado** en modo placa y modo Wokwi.
> - Prueba 05: RX en GPIO 22 e `invertDisplay(true)`. Prueba 03: calibración 1480. Ambas recompiladas.
> - Nueva **`docs/guia-armado.md`**: materiales, tablas de cables, alimentación y armado en 7 fases con prueba en cada una.
> - Documentación revisada: `AGENTS.md` actualizado a 3 zonas, Supabase y hardware real; `README.md`, `plan-hardware.md` (RX 22), `firmware/README.md`, `ESTRUCTURA.md`.
> - La simulación de Wokwi del 2026-10-27 **no quedó guardada** (a propósito, por la clave); se puede rehacer con `firmware/controlador/diagram.json`.
> - En este PC no hay terminal remota (VS Code solo admite clics): las instalaciones las ejecuta el usuario.
> - Pendiente: armar fases 1–7, calibrar sondas, confirmar el tipo de pantalla de la CYD, comprar el 3er DHT22 y confirmar si existen los DS18B20 y las LDR del prototipo antiguo.

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
