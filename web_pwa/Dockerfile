# ============================================================================
# Imagen de la web (React + Vite). Contexto de construcción: la carpeta web_pwa/.
# Dos etapas: (1) compilar con pnpm; (2) servir solo los archivos estáticos con nginx (muy liviano).
# ============================================================================

# ---------- Etapa 1: compilación ----------
# Imagen con Node 22 (versión compatible con Vite 8) en su variante Alpine, pequeña.
FROM node:22-alpine AS construccion

# Carpeta de trabajo de la etapa de compilación.
WORKDIR /app

# Activa corepack, que instala la versión exacta de pnpm indicada en package.json ("packageManager").
RUN corepack enable

# Copia solo los archivos de dependencias primero, para aprovechar la caché de capas de Docker.
COPY package.json pnpm-lock.yaml ./

# Instala las dependencias exactamente como dice pnpm-lock.yaml; falla si el lockfile no coincide con package.json.
RUN pnpm install --frozen-lockfile

# Copia el resto del código de la web.
COPY . .

# Genera los archivos finales en la carpeta dist/.
RUN pnpm build:local

# ---------- Etapa 2: servidor ----------
# nginx en Alpine: usa pocos megabytes de memoria.
FROM nginx:1.27-alpine

# Reemplaza la configuración por defecto de nginx por la del proyecto.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia desde la etapa 1 solo los archivos compilados (sin Node ni dependencias).
COPY --from=construccion /app/dist /usr/share/nginx/html

# Documenta que el servicio escucha en el puerto 80.
EXPOSE 80
