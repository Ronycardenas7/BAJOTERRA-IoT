"""Broker MQTT local en Python (alternativa a Mosquitto cuando NO se puede usar Docker).

Uso (desde la carpeta broker_local, con el entorno virtual activo):
    python broker.py

Lee MQTT_USER, MQTT_PASSWORD y MQTT_PUERTO_HOST del archivo .env de la raiz del proyecto (o de variables de entorno).
Solo escucha en 127.0.0.1 (este equipo). Es para DESARROLLO: no uses este broker para exponer el sistema a la red.
"""

# Permite usar anotaciones de tipo modernas sin importar la version de Python.
from __future__ import annotations

# asyncio: el broker amqtt funciona sobre el bucle de eventos asincrono de Python.
import asyncio
# logging: para mostrar mensajes del broker en pantalla.
import logging
# os: para leer variables de entorno.
import os
# sys: para terminar el programa con un codigo de error claro.
import sys
# tempfile: para crear una carpeta temporal donde guardar el archivo de usuarios (fuera del repositorio).
import tempfile
# Path: manejo de rutas de archivos compatible con Windows y Linux.
from pathlib import Path

# Broker: clase principal del broker MQTT de la libreria amqtt.
from amqtt.broker import Broker
# Argon2Hasher: algoritmo para guardar la contrasena cifrada (nunca en texto plano).
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Carpeta raiz del proyecto: esta en el nivel superior de broker_local/.
RAIZ = Path(__file__).resolve().parent.parent


def leer_env(ruta: Path) -> dict[str, str]:
    """Lee un archivo .env sencillo (CLAVE=valor) y devuelve un diccionario.

    No sobrescribe variables que ya existan en el entorno; solo completa las que faltan.
    """
    # Diccionario donde se guardan los pares clave-valor encontrados.
    valores: dict[str, str] = {}
    # Si el archivo no existe, devuelve el diccionario vacio.
    if not ruta.is_file():
        return valores
    # Recorre cada linea del archivo, leido como UTF-8.
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        # Quita espacios al inicio y al final de la linea.
        linea = linea.strip()
        # Ignora lineas vacias, comentarios y lineas sin signo "=".
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        # Separa en la primera "=": a la izquierda la clave, a la derecha el valor.
        clave, valor = linea.split("=", 1)
        # Guarda la clave y el valor sin espacios sobrantes.
        valores[clave.strip()] = valor.strip()
    # Devuelve todo lo encontrado.
    return valores


def main() -> int:
    """Prepara usuarios y configuracion, y deja el broker funcionando hasta Ctrl+C."""
    # Variables del archivo .env; las del entorno real tienen prioridad.
    env = {**leer_env(RAIZ / ".env"), **os.environ}
    # Usuario y contrasena del broker (deben coincidir con las que usan el backend y el simulador).
    usuario = env.get("MQTT_USER", "")
    clave = env.get("MQTT_PASSWORD", "")
    # Si faltan, se detiene con un mensaje claro en vez de arrancar un broker abierto.
    if not usuario or not clave:
        print("Falta MQTT_USER o MQTT_PASSWORD. Copia .env.example como .env y edita la clave.", file=sys.stderr)
        return 1
    # Puerto donde escuchara el broker (1883 es el estandar de MQTT).
    puerto = int(env.get("MQTT_PUERTO_HOST", "1883"))

    # Carpeta temporal propia de esta ejecucion: el archivo de usuarios no queda dentro del repositorio.
    carpeta = Path(tempfile.mkdtemp(prefix="bajoterra-broker-"))
    # Ruta del archivo de usuarios que leera el plugin de autenticacion.
    archivo_usuarios = carpeta / "usuarios.txt"
    # Genera el hash Argon2 de la contrasena (el archivo no contiene la clave en texto plano).
    hash_clave = PasswordHash((Argon2Hasher(),)).hash(clave)
    # Escribe una linea "usuario:hash" en el archivo.
    archivo_usuarios.write_text(f"{usuario}:{hash_clave}\n", encoding="utf-8")

    # Configuracion del broker, equivalente a docker/mosquitto/mosquitto.conf.
    config = {
        # Un solo listener TCP, solo accesible desde este equipo (127.0.0.1).
        "listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{puerto}"}},
        # Plugins: autenticacion por archivo (sin acceso anonimo) y almacenamiento de mensajes retenidos en memoria.
        "plugins": {
            "amqtt.plugins.authentication.FileAuthPlugin": {"password_file": str(archivo_usuarios)},
        },
    }

    # Formato de los mensajes de registro: hora, nivel y texto.
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
    # Reduce el ruido de la libreria de maquinas de estado.
    logging.getLogger("transitions").setLevel(logging.WARNING)

    async def ejecutar() -> None:
        # Crea el broker con la configuracion de arriba.
        broker = Broker(config)
        # Lo inicia (empieza a aceptar conexiones).
        await broker.start()
        print(f"Broker MQTT local escuchando en 127.0.0.1:{puerto} (usuario: {usuario}). Ctrl+C para detener.")
        try:
            # Espera para siempre; Ctrl+C cancela esta espera.
            await asyncio.Event().wait()
        finally:
            # Al terminar, cierra el broker de forma ordenada.
            await broker.shutdown()

    try:
        # Ejecuta el bucle asincrono hasta que el usuario lo interrumpa.
        asyncio.run(ejecutar())
    except KeyboardInterrupt:
        # Ctrl+C es la forma normal de detenerlo: no es un error.
        pass
    # Codigo 0 = termino bien.
    return 0


# Solo se ejecuta main() si se lanza este archivo directamente.
if __name__ == "__main__":
    sys.exit(main())
