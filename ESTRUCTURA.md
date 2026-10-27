# Estructura del proyecto BAJOTERRA-IoT

Mapa de carpetas y archivos con su función, y los pasos para levantar el proyecto.
Si agregas o mueves archivos, actualiza este documento.

## Cómo levantar el proyecto

Hay tres formas. La **Forma 0 (nube)** es la principal desde la decisión D-010; las otras dos trabajan todo dentro de tu PC.

### Forma 0: en la nube (Supabase), sin broker ni backend

Necesitas Python y Node.js. El simulador necesita `simulador/secretos_nube.conf`, que contiene la clave del dispositivo y no se sube a Git (plantilla: `simulador/secretos_nube.ejemplo.conf`).
La web ya trae la URL y la clave publicable en `web_pwa/src/config/nube.js`. No son secretas.

| Terminal | Comando | Qué hace |
|---|---|---|
| 1 | `cd simulador` y luego `..\.venv\Scripts\python -m sim.nube` | Envía datos SIMULADOS de las 3 zonas a Supabase cada 10 s y ejecuta las órdenes |
| 2 | `cd web_pwa` y luego `corepack pnpm dev` | Web en <http://localhost:5173>: crea tu cuenta, confírmala por correo y entra |

Detalles y permisos de operador: `docs/tiempo-real.md`.

Para las Formas 1 y 2, elige **una**. Ambas necesitan el archivo `.env`: copia `.env.example` como `.env` y cambia `MQTT_PASSWORD`.

### Forma 1: sin Docker (PC de la universidad, Windows)

Necesitas Python 3.12 o superior y Node.js. Usa dos terminales de VS Code (`` Ctrl+` ``, y el botón `+` para abrir la segunda).

**Primera vez:**

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-local.txt
cd web_pwa
$env:COREPACK_ENABLE_DOWNLOAD_PROMPT = "0"
corepack pnpm install --frozen-lockfile
cd ..
```

**Cada vez que trabajes:**

| Terminal | Comando | Qué hace |
|---|---|---|
| 1 | `.venv\Scripts\python scripts\iniciar_local.py` | Inicia broker MQTT + backend + simulador. Espera el mensaje `Listo`. |
| 2 | `cd web_pwa` y luego `corepack pnpm dev:local` | Inicia la web conectada al backend local. Ábrela en <http://localhost:5173> |

Para detener todo: `Ctrl+C` en cada terminal.
**Si cambias código del backend o del simulador, detén la terminal 1 y vuelve a iniciarla:** el código nuevo no se carga solo.

### Forma 2: con Docker (Linux Mint u otro equipo con Docker)

```
docker compose up --build
```

La web queda en <http://localhost:8080>. Para detener: `Ctrl+C` y luego `docker compose down`.

## Mapa del proyecto

```
BAJOTERRA-IoT/
├── AGENTS.md                      Reglas de trabajo del proyecto (stack, idioma, seguridad)
├── ESTRUCTURA.md                  Este documento
├── README.md                      Presentación y guía de uso completa
├── .env.example                   Plantilla de configuración (usuario/clave MQTT, puertos); copiar como .env
├── .gitignore                     Archivos que Git NO sube (.env, node_modules, secretos.h...)
├── .gitattributes                 Fija los finales de línea (LF) para que funcione en Windows y Linux
├── requirements-local.txt         Dependencias de Python para correr todo sin Docker
├── docker-compose.yml             Levanta broker, backend, simulador y web con Docker
│
├── backend/                       API en Python (Flask): recibe datos por MQTT y los entrega a la web
│   ├── run.py                     Inicia el backend en modo desarrollo (puerto 5000)
│   ├── requirements.txt           Librerías del backend (Flask, paho-mqtt, gunicorn)
│   ├── requirements-dev.txt       Lo anterior + pytest para las pruebas
│   ├── pytest.ini                 Configuración de las pruebas
│   ├── Dockerfile / .dockerignore Imagen Docker del backend
│   ├── app/
│   │   ├── __init__.py            Crea la aplicación y conecta todas las capas (inyección de dependencias)
│   │   ├── config/ajustes.py      Lee la configuración desde variables de entorno
│   │   ├── domain/                Reglas del negocio, sin dependencias externas
│   │   │   ├── constantes.py      Zonas (árida, húmeda, selvática), mediciones, rangos, unidades y actuadores
│   │   │   ├── modelos.py         Clases: lectura de zona, lectura de depósito, estado de dispositivo, comando
│   │   │   ├── errores.py         Errores propios (dato inválido, no encontrado...)
│   │   │   └── tiempo.py          Fechas siempre en UTC
│   │   ├── schemas/mensajes.py    Valida cada mensaje MQTT (rangos, tipos, campos desconocidos)
│   │   ├── mqtt/
│   │   │   ├── temas.py           Arma y lee los temas MQTT (bajoterra/01/zonas/...)
│   │   │   ├── manejadores.py     Qué hacer con cada mensaje que llega
│   │   │   └── publicador.py      Envía comandos a los dispositivos
│   │   ├── infrastructure/broker_mqtt.py   Conexión real con el broker (reconexión automática)
│   │   ├── repositories/
│   │   │   ├── base.py            Interfaces de almacenamiento (permiten cambiar a Supabase sin tocar el resto)
│   │   │   └── memoria.py         Almacenamiento temporal en memoria (se pierde al reiniciar)
│   │   ├── services/
│   │   │   ├── telemetria_service.py   Resumen de zonas, historial y detección de datos viejos
│   │   │   └── comandos_service.py     Ciclo de vida de una orden: enviada → confirmada / caducada
│   │   └── api/
│   │       ├── rutas.py           Direcciones HTTP: /salud, /api/resumen, /api/zonas/..., /api/comandos/...
│   │       └── errores.py         Respuestas de error con formato común
│   └── tests/                     Pruebas automáticas del backend (pytest)
│
├── simulador/                     Reemplaza al ESP32 mientras no hay hardware: genera datos SIMULADOS
│   ├── sim/
│   │   ├── __main__.py            Permite ejecutar "python -m sim"
│   │   ├── main.py                Crea las 3 zonas y el depósito y publica cada pocos segundos
│   │   ├── config.py              Configuración del simulador (intervalo, semilla, límites)
│   │   ├── modelos.py             Física simplificada de cada zona (temperatura, humedad, CO₂, LED...)
│   │   ├── dispositivos.py        Cliente MQTT de cada dispositivo simulado (incluye "última voluntad")
│   │   ├── nube.py                Modo nube: envía lecturas a Supabase por HTTPS y atiende órdenes (python -m sim.nube)
│   │   └── tiempo.py              Fechas en UTC
│   ├── secretos_nube.ejemplo.conf Plantilla de secretos_nube.conf (clave del simulador en modo nube; no se sube a Git)
│   ├── tests/                     Pruebas automáticas del simulador
│   └── requirements*.txt, pytest.ini, Dockerfile, .dockerignore
│
├── broker_local/                  Broker MQTT en Python para trabajar SIN Docker
│   ├── broker.py                  Inicia el broker con usuario/clave del .env (solo en este PC)
│   └── requirements.txt           Librería amqtt
│
├── scripts/
│   └── iniciar_local.py           Inicia broker + backend + simulador con un solo comando (sin Docker)
│
├── docker/mosquitto/mosquitto.conf   Configuración del broker Mosquitto (modo Docker)
│
├── web_pwa/                       Web en React + Vite (página de inicio y Panel de Control)
│   ├── index.html                 Página base; carga el código de React
│   ├── package.json / pnpm-lock.yaml   Dependencias de la web (se instalan con pnpm)
│   ├── vite.config.js             Servidor de desarrollo y redirección de /api al backend
│   ├── nginx.conf / Dockerfile    Servidor de la web en modo Docker
│   ├── public/
│   │   ├── icono.svg              Icono de la pestaña y de la app
│   │   └── manifest.webmanifest   Datos para instalar la web como app (PWA)
│   └── src/
│       ├── main.jsx               Punto de entrada de React
│       ├── app/
│       │   ├── App.jsx            Estructura general: barra, página actual y pie
│       │   └── useRuta.js         Navegación entre Inicio y Panel (#/panel) sin librerías
│       ├── components/            Piezas reutilizables
│       │   ├── Encabezado.jsx     Barra fija con efecto vidrio y botón "Panel de Control"
│       │   ├── Pie.jsx            Pie de página
│       │   ├── Iconos.jsx         Iconos SVG propios
│       │   ├── Etiqueta.jsx       Etiquetas de estado (SIMULADO, En línea...)
│       │   └── LimiteDeError.jsx  Evita la página en blanco si algo falla
│       ├── pages/
│       │   ├── Inicio.jsx         Página de inicio (une las secciones)
│       │   ├── inicio/            Secciones: Hero, Proyecto, Capacidades, ZonasEvaluacion, Variables, LlamadaFinal
│       │   └── Panel.jsx          Panel de Control: 3 zonas + depósito
│       ├── features/
│       │   ├── zonas/zonas.js     Nombre, color, descripción y métricas destacadas de cada zona
│       │   ├── zonas/TarjetaZona.jsx       Tarjeta de una zona en el panel
│       │   ├── telemetria/useResumen.js    Consulta el backend cada 3 s y guarda el historial para los gráficos
│       │   ├── telemetria/Metrica.jsx      Recuadro de una medición con su gráfico
│       │   ├── telemetria/Sparkline.jsx    Gráfico de línea liviano (SVG)
│       │   ├── telemetria/TarjetaDeposito.jsx  Tarjeta del depósito de agua
│       │   ├── telemetria/formato.js       Formato de números, horas (UTC → Chile) y estados
│       │   ├── actuadores/PanelActuadores.jsx  Bomba, extractor y luces LED con sus botones
│       │   └── actuadores/useComando.js        Envía una orden y sigue su confirmación
│       ├── services/api.js        Comunicación con el backend local (o con Supabase en modo nube)
│       ├── config/nube.js         URL y clave PUBLICABLE de Supabase (no son secretas)
│       ├── services/supabase.js   Cliente de Supabase; modo nube por defecto, modo local con "pnpm dev:local"
│       ├── services/datosNube.js  Consultas, tiempo real (Realtime), órdenes y hora del servidor en Supabase
│       ├── features/sesion/       Inicio de sesión (Acceso.jsx) y sesión/permiso de operador (useSesion.js)
│       ├── features/telemetria/useResumenNube.js  Datos del panel en modo nube (Realtime + corrección del reloj)
│       └── styles/global.css      Todos los estilos (tema oscuro, colores por zona)
│
├── firmware/                      Código del ESP32 (Arduino C++)
│   ├── README.md                  Cómo probar en Wokwi o en una placa real
│   ├── controlador/               Firmware principal v1 de la DevKit (3 zonas, control local, nube, UART a la CYD)
│   │   ├── controlador.ino        Programa principal
│   │   ├── config.h               Pines, zonas, umbrales y tiempos
│   │   ├── secretos.ejemplo.h     Plantilla de secretos.h (no se sube)
│   │   └── diagram.json, libraries.txt  Circuito y bibliotecas para Wokwi
│   ├── prueba_01_wifi/
│   │   ├── prueba_01_wifi.ino     Prueba 01: WiFi + hora UTC por internet
│   │   ├── secretos.ejemplo.h     Plantilla de credenciales WiFi (copiar como secretos.h)
│   │   └── diagram.json           Circuito para el simulador Wokwi
│   ├── prueba_03_sensores/        Prueba 03 (DevKit): DHT22 + 3 sondas de suelo con calibración
│   ├── prueba_04_reles/           Prueba 04 (DevKit): 4 relés (2 bombas, 2 ventiladores) con límites de seguridad
│   ├── prueba_05_pantalla_cyd/    Prueba 05 (CYD ESP32-2432S028): pantalla con las 3 zonas, LDR y UART
│   └── prueba_02_supabase/
│       ├── prueba_02_supabase.ino Prueba 02: lecturas a Supabase por HTTPS y órdenes (LED = luces)
│       ├── secretos.ejemplo.h     Plantilla: WiFi, Supabase y clave del dispositivo (copiar como secretos.h)
│       ├── diagram.json           Circuito para Wokwi
│       └── libraries.txt          Bibliotecas que Wokwi instala (ArduinoJson)
│
├── supabase/migrations/           Base de datos en la nube (APLICADAS en el proyecto bajoterra-iot)
│   ├── 0001_esquema_inicial.sql   Tablas de lecturas y órdenes
│   ├── 0002_ingesta_y_tiempo_real.sql   Dispositivos, claves, funciones de ingesta/órdenes, permisos, RLS y Realtime
│   └── 0003_hora_servidor.sql     Hora del servidor (corrige relojes de PC desfasados)
│
└── docs/
    ├── decisiones.md              Registro de decisiones de arquitectura (D-001...)
    ├── estado-actual.md           Qué está hecho, qué se verificó y qué falta
    ├── mqtt-topics.md             Contrato de mensajes: temas, campos, unidades y rangos
    ├── tiempo-real.md             Cómo llegarán los datos del ESP32 a cualquier dispositivo
    └── plan-hardware.md           Inventario, pines, cableado, alimentación y fases con el hardware real
```

## Carpetas que se crean solas (no se suben a Git)

| Carpeta | Qué es |
|---|---|
| `.venv/` | Entorno virtual de Python con las librerías instaladas |
| `web_pwa/node_modules/` | Librerías de la web instaladas por pnpm |
| `web_pwa/dist/` | Web compilada (`pnpm build`) |
| `__pycache__/`, `.pytest_cache/` | Archivos temporales de Python |
