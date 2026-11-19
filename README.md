# BAJOTERRA-IoT

Invernadero de tres zonas (árida, húmeda y selvática) y un depósito principal. Los nodos envían mediciones al ESP32 Maestro por ESP-NOW. El Maestro envía telemetría a Supabase por HTTPS y se comunica con la pantalla táctil CYD por UART.

La web usa React 19 y Vite 8. El panel lee los datos desde Supabase Realtime y los operadores autorizados pueden enviar órdenes de bomba, extractor y temperatura objetivo.

## Desarrollo web

Desde la raíz del repositorio, con Node.js y Corepack disponibles:

```powershell
cd web_pwa
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Abre http://127.0.0.1:5173/#/panel e inicia sesión. Para generar la compilación de producción ejecuta `corepack pnpm build` desde `web_pwa/`.

## Despliegue en Vercel

Importa el repositorio con el preset **Vite**, la **Root Directory** en `web_pwa` y la salida en `dist`. Para usar Corepack, configura `ENABLE_EXPERIMENTAL_COREPACK=1` en Vercel. El proyecto fija pnpm en `web_pwa/package.json`.

El archivo `web_pwa/vercel.json` configura el respaldo de la SPA. Después del despliegue, abre y recarga `/#/panel` para comprobar que carga el acceso.

## Documentación

- [Estructura del proyecto](ESTRUCTURA.md)
- [Armado y cableado](docs/guia-armado.md)
- [Telemetría, sesión y permisos](docs/tiempo-real.md)
