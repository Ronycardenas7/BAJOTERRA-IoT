# BAJOTERRA-IoT

Invernadero automatizado con **tres zonas de evaluación independientes** (árida, húmeda y selvática). Este repositorio contiene la base del sistema:
un **broker MQTT**, un **backend** (Flask), un **simulador** que reemplaza al ESP32 mientras no hay hardware, y una **web** (React) para ver los datos.

> **Todos los datos que muestra hoy el sistema son SIMULADOS.** La web los marca con la etiqueta "SIMULADO". Todavía no hay hardware ni Supabase conectados.

```
 Simulador  --MQTT-->  Mosquitto  --MQTT-->  Backend (Flask)  <--HTTP--  Web (React + nginx)
 (sustituye              (broker)             guarda en memoria
  al ESP32)
```

> Mapa de carpetas y archivos, y pasos rápidos para levantar el proyecto: **[ESTRUCTURA.md](ESTRUCTURA.md)**.
> Cómo llegarán los datos del ESP32 a cualquier dispositivo: **[docs/tiempo-real.md](docs/tiempo-real.md)**.

## Modo nube (Supabase) — principal desde el 2026-10-27

Los datos van del ESP32 (o del simulador) a **Supabase** por HTTPS y la web los recibe **en tiempo real**, con inicio de sesión.
Cómo funciona, seguridad y permisos de operador: **[docs/tiempo-real.md](docs/tiempo-real.md)**. Comandos para levantarlo: **[ESTRUCTURA.md](ESTRUCTURA.md)** (Forma 0).
Lo de abajo describe el modo local (broker + backend en tu PC), que sigue sirviendo para desarrollar sin internet.

## Requisitos

Dos formas de ejecutarlo: **con Docker** (abajo) o **sin Docker** (sección "Sin Docker", más adelante).

- **Docker** con Docker Compose v2 (`docker compose version` debe funcionar).
- Nada más: Python, Node y pnpm van dentro de las imágenes.

## Inicio rápido (con Docker)

1. **Crear el archivo de configuración local.** Copia el ejemplo; el `.env` real nunca se sube a Git.
   - Windows (CMD): `copy .env.example .env`
   - Linux / macOS / PowerShell: `cp .env.example .env`
2. **Cambiar la contraseña del broker** editando `MQTT_PASSWORD` en `.env` (es solo local, pero no dejes la del ejemplo).
3. **Construir y levantar todo:**
   ```
   docker compose up --build
   ```
   `up` crea e inicia los contenedores y `--build` construye las imágenes la primera vez (puede tardar varios minutos).
4. **Abrir la web:** <http://localhost:8080>
5. **Detener:** `Ctrl+C`, y para eliminar los contenedores: `docker compose down`.

| Servicio | Dirección (solo este equipo) | Para qué |
|---|---|---|
| Web | <http://localhost:8080> | Página de inicio y Panel de Control (`#/panel`) con las tres zonas y el depósito |
| Backend | <http://localhost:5000/salud> | Comprobar que la API responde |
| Broker MQTT | `localhost:1883` (usuario y clave del `.env`) | Depurar con `mosquitto_sub` |

Comandos útiles:

```
docker compose ps                      # estado y salud de cada servicio
docker compose logs -f backend         # ver los registros del backend en vivo
docker stats --no-stream               # medir el consumo real de memoria
docker compose down                    # apagar y eliminar contenedores
```

## Sin Docker (Windows, sin permisos de administrador)

Para equipos donde no se puede instalar Docker (por ejemplo, un PC de la universidad). Necesitas **Python 3.12 o superior** y **Node.js**; no hace falta instalar nada más.
En lugar de Mosquitto se usa `broker_local/`, un broker MQTT escrito en Python (librería `amqtt`) que también exige usuario y contraseña y solo escucha en este equipo.

Todos los comandos se ejecutan en PowerShell (o en la terminal de VS Code), dentro de la carpeta del proyecto.

Puedes usar la terminal integrada de VS Code (`` Ctrl+` ``): son los mismos comandos. Usa una terminal para los servicios y otra (botón `+`) para la web.

**1. Crear la configuración** (si aún no lo hiciste) y poner tu contraseña en `MQTT_PASSWORD`:
```
copy .env.example .env
```

**2. Crear el entorno virtual e instalar las dependencias** (una sola vez). Se llama directamente a `python.exe` del entorno para no depender de "activar" nada:
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-local.txt
```

**3. Iniciar broker + backend + simulador con un solo comando** (déjalo abierto; `Ctrl+C` detiene todo):
```
.venv\Scripts\python scripts\iniciar_local.py
```
Comprueba que el backend responde en <http://127.0.0.1:5000/salud>.

**4. Iniciar la web** en **otra** ventana de PowerShell (primera vez: instala dependencias). `corepack` viene con Node y usa la versión de pnpm fijada en `package.json`:
```
cd web_pwa
$env:COREPACK_ENABLE_DOWNLOAD_PROMPT = "0"
corepack pnpm install --frozen-lockfile
corepack pnpm dev:local
```
Abre la dirección que muestra la consola (normalmente <http://localhost:5173>).

Si `corepack` pide permisos o falla, dímelo con el mensaje exacto: hay alternativas.

> Diferencias con Docker: no hay límites de memoria por servicio y el backend usa el servidor de desarrollo de Flask (no gunicorn, que no corre en Windows).
> Al detenerlo, Windows cierra los programas de forma abrupta; el broker lo detecta y marca los dispositivos como desconectados, así que la web lo refleja igual.
> Este modo es **solo para desarrollo local**.

## Qué verás

- **Página de inicio** con barra fija (efecto vidrio), presentación del proyecto y las tres zonas, y acceso al **Panel de Control**.
- **Panel de Control** con una tarjeta por zona, cada una con sus mediciones destacadas y un mini gráfico de tendencia: **árida** (temperatura, humedad del sustrato, radiación solar), **húmeda** (humedad del aire y del sustrato) y **selvática** (CO₂, luz difusa). Además, el estado **reportado** de la bomba de agua, el extractor y las luces LED.
- Tarjeta del **depósito** con conductividad (EC) y disponibilidad de agua.
- Botones para pedir encender/apagar bomba de agua, extractor y luces LED. Una orden es solo una **solicitud**: queda "enviada" hasta que el dispositivo confirma.
  Los botones se bloquean si el dispositivo no está en línea o sus datos están desactualizados.
- Un valor ausente aparece como "Sin dato" (nunca como 0). Las horas se muestran en la zona horaria de Santiago; internamente todo es UTC.

## Desarrollo sin Docker (opcional)

Útil para depurar. Necesitas un broker MQTT accesible (por ejemplo, solo el servicio `mosquitto` con `docker compose up mosquitto`).

```
# Backend (Python 3.12)
cd backend
python -m venv .venv                   # crea un entorno virtual aislado
# Windows: .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt    # dependencias + pytest
pytest                                 # ejecuta las pruebas

# Simulador
cd simulador
pip install -r requirements-dev.txt
pytest

# Web (solo pnpm; no uses npm ni yarn)
cd web_pwa
corepack enable                        # activa pnpm con la versión fijada en package.json
pnpm install --frozen-lockfile         # instala exactamente lo del pnpm-lock.yaml
pnpm dev:local                         # web conectada al backend local ("pnpm dev" = modo nube)
```

Las variables que lee cada programa están en `.env.example` y en `backend/app/config/ajustes.py` / `simulador/sim/config.py`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `backend/` | API Flask por capas: `api` → `services` → `repositories`, más `mqtt`, `schemas`, `domain`, `infrastructure`, `config` |
| `simulador/` | Simula 2 zonas y 1 depósito con modelos simples y control con histéresis |
| `web_pwa/` | React + Vite (JavaScript), organizada por funcionalidades |
| `docker/` | Configuración del broker Mosquitto |
| `broker_local/` | Broker MQTT en Python para usar **sin Docker** |
| `scripts/` | `iniciar_local.py`: arranca broker, backend y simulador sin Docker |
| `supabase/` | Borrador del esquema SQL (**no aplicado**) |
| `firmware/` | Código del ESP32; primera prueba: `prueba_01_wifi/` (WiFi + hora UTC) |
| `docs/` | `mqtt-topics.md` (contrato de mensajes), `decisiones.md`, `estado-actual.md` |

## Consumo de memoria

La suma de los límites configurados es de 352 MB (mosquitto 64, backend 192, simulador 64, web 32). Es una estimación: **mídela** con `docker stats`.
En Windows, Docker Desktop (WSL2) puede reservar mucha RAM; puedes limitarla creando `%UserProfile%\.wslconfig` con:

```
[wsl2]
memory=1GB
```

y ejecutando `wsl --shutdown`. En Linux, Docker Engine usa bastante menos que Docker Desktop.

## Problemas frecuentes

- **"Falta MQTT_USER en el archivo .env"**: no creaste el `.env` (paso 1).
- **Puerto ocupado** (1883, 5000 u 8080): cambia `MQTT_PUERTO_HOST`, `BACKEND_PUERTO_HOST` o `WEB_PUERTO_HOST` en `.env`.
- **La web dice "Sin datos" o "Desactualizado"**: espera unos segundos tras arrancar; revisa `docker compose ps` y `docker compose logs simulador backend`.
- **Cambié la contraseña y el broker no acepta a los demás**: reinicia todo con `docker compose down` y `docker compose up`.

## Seguridad

- El `.env` está en `.gitignore`; no subas credenciales. Los valores de `.env.example` son ficticios.
- Los puertos se publican solo en `127.0.0.1`. No los expongas a la red sin agregar TLS y control de acceso por tema en Mosquitto.
- Los contenedores del backend y el simulador corren sin privilegios (usuario no root, sin capacidades del kernel).

## Estado y próximos pasos

Ver `docs/estado-actual.md`. En resumen: falta conectar **Supabase** (hoy el backend guarda en memoria), decidir la topología **ESP-NOW** (nodos + gateway o MQTT directo)
y la del **depósito**, y escribir el firmware del ESP32 cuando haya hardware.
