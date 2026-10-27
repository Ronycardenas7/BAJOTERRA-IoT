# Punto de composición del backend: crea la aplicación Flask y conecta todas las capas entre sí.
# Aquí (y solo aquí) se deciden las implementaciones concretas: repositorios en memoria, cliente MQTT real, etc.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# atexit ejecuta una función cuando el programa termina.
import atexit
# logging configura y escribe mensajes de diagnóstico.
import logging
# dataclass crea una clase de solo datos.
from dataclasses import dataclass

# Flask es la clase de la aplicación web.
from flask import Flask

# Blueprint de rutas y registro de errores (capa API).
from app.api.errores import registrar_manejadores_errores
from app.api.rutas import crear_blueprint
# Ajustes leídos del entorno.
from app.config.ajustes import Ajustes
# Cliente real del broker MQTT.
from app.infrastructure.broker_mqtt import ClienteMqtt
# Adaptadores MQTT.
from app.mqtt.manejadores import ManejadorMensajes
from app.mqtt.publicador import PublicadorComandosMqtt
from app.mqtt.temas import Temas
# Repositorios en memoria.
from app.repositories.memoria import (
    RepositorioComandosMemoria,
    RepositorioDispositivosMemoria,
    RepositorioTelemetriaMemoria,
)
# Servicios (casos de uso).
from app.services.comandos_service import ServicioComandos
from app.services.telemetria_service import ServicioTelemetria

# Versión del backend (se muestra al arrancar).
VERSION = "0.1.0"


# Agrupa los componentes que las rutas necesitan.
@dataclass(frozen=True)
class Contenedor:
    # Servicio de telemetría.
    telemetria: ServicioTelemetria
    # Servicio de comandos.
    comandos: ServicioComandos
    # Cliente MQTT (las rutas solo consultan si está conectado).
    cliente_mqtt: object


# Fábrica de la aplicación. Se puede llamar con un cliente MQTT falso para hacer pruebas sin broker.
def create_app(ajustes: Ajustes | None = None, cliente_mqtt: object | None = None) -> Flask:
    # Si no se pasan ajustes, se leen del entorno.
    ajustes = ajustes or Ajustes.desde_entorno()
    # Configura el formato de los logs para toda la aplicación.
    logging.basicConfig(level=ajustes.nivel_log, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Crea la aplicación Flask.
    app = Flask(__name__)
    # Mantiene el orden de los campos tal como se escribieron en las respuestas JSON.
    app.json.sort_keys = False

    # Repositorios (hoy en memoria).
    repo_telemetria = RepositorioTelemetriaMemoria(ajustes.max_lecturas)
    repo_dispositivos = RepositorioDispositivosMemoria()
    repo_comandos = RepositorioComandosMemoria(ajustes.max_comandos)

    # Constructor de temas MQTT.
    temas = Temas(ajustes.mqtt_prefijo)
    # Si no se entregó un cliente (uso normal), crea el cliente real y recuerda que hay que iniciarlo.
    iniciar_cliente = cliente_mqtt is None
    # Cliente MQTT real o el que se haya inyectado.
    cliente = cliente_mqtt or ClienteMqtt(
        host=ajustes.mqtt_host,
        puerto=ajustes.mqtt_puerto,
        usuario=ajustes.mqtt_usuario,
        clave=ajustes.mqtt_clave,
        client_id=ajustes.mqtt_client_id,
    )

    # Servicios con sus dependencias inyectadas.
    servicio_telemetria = ServicioTelemetria(repo_telemetria, repo_dispositivos, ajustes.umbral_desactualizado_s)
    servicio_comandos = ServicioComandos(repo_comandos, PublicadorComandosMqtt(cliente, temas), ajustes.ttl_comando_s)

    # Suscribe los manejadores MQTT al cliente.
    ManejadorMensajes(servicio_telemetria, servicio_comandos, temas).registrar(cliente)

    # Guarda los componentes para que las rutas los encuentren.
    app.extensions["bajoterra"] = Contenedor(servicio_telemetria, servicio_comandos, cliente)
    # Registra las rutas HTTP.
    app.register_blueprint(crear_blueprint())
    # Registra el formato común de errores.
    registrar_manejadores_errores(app)

    # Solo con cliente real: inicia la conexión y asegura el cierre ordenado al terminar el proceso.
    if iniciar_cliente:
        # Inicia la conexión en segundo plano.
        cliente.iniciar()
        # Al terminar el programa, cierra la conexión.
        atexit.register(cliente.detener)
    # Deja constancia del arranque.
    logging.getLogger(__name__).info("Backend BAJOTERRA %s listo", VERSION)
    # Devuelve la aplicación.
    return app
