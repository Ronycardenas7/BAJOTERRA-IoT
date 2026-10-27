# ============================================================================
# Imagen del simulador de dispositivos (Python + paho-mqtt). Contexto: la carpeta simulador/.
# ============================================================================

# Imagen base: Python 3.12 en versión "slim".
FROM python:3.12-slim

# No escribe .pyc, muestra logs de inmediato y deja pip sin caché ni avisos de versión.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Carpeta de trabajo dentro del contenedor.
WORKDIR /app

# Usuario sin privilegios para ejecutar el simulador.
RUN useradd --system --no-create-home --uid 10001 bajoterra

# Copia solo las dependencias primero para aprovechar la caché de capas.
COPY requirements.txt ./

# Instala paho-mqtt con versión exacta.
RUN pip install -r requirements.txt

# Copia el código del simulador (paquete "sim").
COPY sim ./sim

# Ejecuta como usuario sin privilegios.
USER bajoterra

# Arranque: "python -m sim" ejecuta sim/__main__.py. Al recibir SIGTERM (docker stop) se desconecta avisando al broker.
CMD ["python", "-m", "sim"]
