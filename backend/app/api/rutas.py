# Rutas HTTP (capa de entrada). Solo traducen petición -> servicio -> respuesta JSON; no contienen reglas de negocio.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# Blueprint agrupa rutas; current_app da acceso a la aplicación; jsonify crea respuestas JSON; request lee la petición.
from flask import Blueprint, current_app, jsonify, request

# Error de datos inválidos para validar la petición.
from app.domain.errores import DatosInvalidos

# Límite máximo de elementos que se puede pedir en un historial.
LIMITE_MAXIMO = 720
# Cantidad de elementos que se devuelve si no se indica límite.
LIMITE_DEFECTO = 60


# Devuelve el contenedor con los servicios, guardado en la aplicación al crearla.
def _contenedor():
    # extensions es un diccionario donde la aplicación guarda sus componentes.
    return current_app.extensions["bajoterra"]


# Lee el parámetro "limite" de la URL y lo valida.
def _leer_limite() -> int:
    # Obtiene el texto del parámetro (o el valor por defecto).
    crudo = request.args.get("limite", str(LIMITE_DEFECTO))
    # Intenta convertirlo a entero.
    try:
        # int() lanza ValueError si no es un número entero.
        limite = int(crudo)
    # Captura el texto no numérico.
    except ValueError:
        # Error 400 claro.
        raise DatosInvalidos("'limite' debe ser un número entero") from None
    # Comprueba el rango permitido.
    if not 1 <= limite <= LIMITE_MAXIMO:
        # Error 400 con el rango válido.
        raise DatosInvalidos(f"'limite' debe estar entre 1 y {LIMITE_MAXIMO}")
    # Devuelve el límite validado.
    return limite


# Crea el blueprint con todas las rutas.
def crear_blueprint() -> Blueprint:
    # Blueprint llamado "api".
    api = Blueprint("api", __name__)

    # GET /salud: indica si el backend está vivo y si tiene conexión con el broker.
    @api.get("/salud")
    def salud():
        # Estado de la conexión MQTT.
        mqtt_conectado = _contenedor().cliente_mqtt.conectado
        # "ok" si todo está bien; "degradado" si el backend vive pero no tiene broker.
        return jsonify({"estado": "ok" if mqtt_conectado else "degradado", "mqtt_conectado": mqtt_conectado})

    # GET /api/resumen: última lectura y conexión de cada zona y depósito.
    @api.get("/api/resumen")
    def resumen():
        # El servicio arma el resumen; jsonify lo convierte en JSON.
        return jsonify(_contenedor().telemetria.resumen())

    # GET /api/zonas/<zona>/telemetria: historial reciente de una zona.
    @api.get("/api/zonas/<zona>/telemetria")
    def historial(zona: str):
        # Pide el historial con el límite validado.
        lecturas = _contenedor().telemetria.historial_zona(zona, _leer_limite())
        # Responde con la zona y sus lecturas.
        return jsonify({"zona": zona, "lecturas": lecturas})

    # POST /api/zonas/<zona>/comandos: solicita una orden a un actuador.
    @api.post("/api/zonas/<zona>/comandos")
    def solicitar_comando(zona: str):
        # Lee el cuerpo JSON (silent=True devuelve None si es inválido en vez de lanzar un error).
        cuerpo = request.get_json(silent=True)
        # El cuerpo debe ser un objeto JSON.
        if not isinstance(cuerpo, dict):
            # Error 400 claro.
            raise DatosInvalidos("el cuerpo debe ser un objeto JSON con 'actuador' y 'estado'")
        # El servicio valida los valores, registra y publica la orden.
        comando = _contenedor().comandos.solicitar(
            zona=zona,
            actuador=cuerpo.get("actuador"),
            estado=cuerpo.get("estado"),
            ttl_s=cuerpo.get("ttl_segundos"),
        )
        # 202 Accepted: la orden fue aceptada y enviada, pero aún NO está ejecutada.
        return jsonify({"comando": comando.a_dict()}), 202

    # GET /api/zonas/<zona>/comandos: últimos comandos de una zona.
    @api.get("/api/zonas/<zona>/comandos")
    def listar_comandos(zona: str):
        # Pide los comandos con el límite validado.
        comandos = _contenedor().comandos.listar_zona(zona, _leer_limite())
        # Responde con la zona y sus comandos.
        return jsonify({"zona": zona, "comandos": [c.a_dict() for c in comandos]})

    # GET /api/comandos/<id_comando>: estado de un comando concreto.
    @api.get("/api/comandos/<id_comando>")
    def ver_comando(id_comando: str):
        # Busca el comando (lanza 404 si no existe).
        comando = _contenedor().comandos.obtener(id_comando)
        # Responde con el comando.
        return jsonify({"comando": comando.a_dict()})

    # Devuelve el blueprint ya armado.
    return api
