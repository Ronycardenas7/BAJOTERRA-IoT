# ============================================================================
# Imagen del backend (Python + Flask + gunicorn). Contexto de construcción: la carpeta backend/.
# ============================================================================

# Imagen base: Python 3.12 en versión "slim" (pequeña, basada en Debian).
FROM python:3.12-slim

# No escribe archivos .pyc dentro de la imagen.
ENV PYTHONDONTWRITEBYTECODE=1 \
    # Muestra los logs de inmediato (sin guardarlos en un búfer), para verlos con "docker compose logs".
    PYTHONUNBUFFERED=1 \
    # pip no guarda caché de descargas: la imagen queda más liviana.
    PIP_NO_CACHE_DIR=1 \
    # pip no comprueba si hay una versión nueva de sí mismo.
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Carpeta de trabajo dentro del contenedor.
WORKDIR /app

# Crea un usuario sin privilegios (el backend NO debe correr como administrador dentro del contenedor).
RUN useradd --system --no-create-home --uid 10001 bajoterra

# Copia primero solo la lista de dependencias: si no cambia, Docker reutiliza la capa instalada y construye más rápido.
COPY requirements.txt ./

# Instala las dependencias de ejecución (Flask, paho-mqtt, gunicorn) con versiones exactas.
RUN pip install -r requirements.txt

# Copia el código de la aplicación.
COPY app ./app

# A partir de aquí todo se ejecuta como el usuario sin privilegios.
USER bajoterra

# Documenta que el servicio escucha en el puerto 5000.
EXPOSE 5000

# Comando de arranque: gunicorn con UN solo proceso (el cliente MQTT debe existir una sola vez) y 4 hilos para atender peticiones.
# "app:create_app()" le dice a gunicorn que construya la aplicación llamando a la fábrica create_app().
# --worker-tmp-dir /dev/shm usa memoria para los archivos temporales de gunicorn (recomendado en Docker).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "app:create_app()"]
