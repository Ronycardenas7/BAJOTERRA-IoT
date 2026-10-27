# Adaptador que traduce un Comando del dominio a un mensaje MQTT.
# Cumple el contrato PublicadorComandos del servicio, sin que el servicio conozca MQTT.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# Entidad Comando.
from app.domain.modelos import Comando
# Utilidad para convertir fechas a texto UTC.
from app.domain.tiempo import a_iso
# Constructor de temas.
from app.mqtt.temas import Temas


# Publica comandos en el broker.
class PublicadorComandosMqtt:
    # Recibe el cliente MQTT (algo con un método "publicar") y el constructor de temas.
    def __init__(self, cliente, temas: Temas) -> None:
        # Cliente MQTT a través del cual se publica.
        self._cliente = cliente
        # Constructor de temas.
        self._temas = temas

    # Publica el comando en el tema de comandos de su zona.
    def enviar(self, comando: Comando) -> None:
        # Cuerpo del mensaje según el contrato: id, zona, actuador, estado pedido y caducidad.
        carga = {
            "id_comando": comando.id_comando,
            "zona": comando.zona,
            "actuador": comando.actuador,
            "estado_solicitado": comando.estado_solicitado,
            "solicitado_en": a_iso(comando.solicitado_en),
            "caduca_en": a_iso(comando.caduca_en),
        }
        # QoS 1 = el broker confirma la recepción. retain=False = NUNCA se guarda para reenviarlo después,
        # así un dispositivo que se reconecta no repite órdenes viejas (puede ser peligroso con bombas).
        self._cliente.publicar(self._temas.comandos_zona(comando.zona), carga, qos=1, retain=False)
