# Arranque para DESARROLLO local sin Docker: python run.py
# En Docker se usa gunicorn (ver backend/Dockerfile); este servidor integrado NO es para producción.

# Importa la fábrica de la aplicación.
from app import create_app

# Solo se ejecuta si el archivo se lanza directamente (no al importarlo).
if __name__ == "__main__":
    # Crea la aplicación leyendo la configuración de las variables de entorno.
    aplicacion = create_app()
    # host=127.0.0.1: solo accesible desde este equipo. use_reloader=False evita crear dos clientes MQTT.
    aplicacion.run(host="127.0.0.1", port=5000, use_reloader=False)
