# Configuración de ejecución del backend: lee variables de entorno y las valida al arrancar.
# Si una variable tiene un valor inválido, el programa falla de inmediato con un mensaje claro.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# "os" da acceso a las variables de entorno del sistema.
import os
# "Mapping" es el tipo de un diccionario de solo lectura (como os.environ).
from collections.abc import Mapping
# "dataclass" crea una clase de solo datos sin escribir el constructor a mano.
from dataclasses import dataclass


# Lee una variable de entorno como número entero y comprueba que esté dentro de un rango.
def _entero(entorno: Mapping[str, str], nombre: str, defecto: int, minimo: int, maximo: int) -> int:
    # Busca la variable; si no existe usa el valor por defecto (convertido a texto).
    crudo = entorno.get(nombre, str(defecto))
    # Intenta convertir el texto a entero.
    try:
        # int() lanza ValueError si el texto no es un entero válido.
        valor = int(crudo)
    # Captura solo el error de conversión.
    except ValueError:
        # Relanza con un mensaje que dice qué variable está mal y qué valor tenía.
        raise ValueError(f"La variable {nombre} debe ser un entero, pero vale {crudo!r}") from None
    # Comprueba que el número esté dentro del rango permitido.
    if not minimo <= valor <= maximo:
        # Si no lo está, informa el rango válido.
        raise ValueError(f"La variable {nombre} debe estar entre {minimo} y {maximo}, pero vale {valor}")
    # Devuelve el entero ya validado.
    return valor


# frozen=True: los ajustes no cambian mientras el programa corre.
@dataclass(frozen=True)
class Ajustes:
    # Nombre o IP del broker MQTT (dentro de Docker es el nombre del servicio: "mosquitto").
    mqtt_host: str = "localhost"
    # Puerto TCP del broker MQTT.
    mqtt_puerto: int = 1883
    # Usuario MQTT; vacío significa "sin autenticación" (solo para pruebas locales).
    mqtt_usuario: str = ""
    # Contraseña MQTT. Nunca se imprime en los logs.
    mqtt_clave: str = ""
    # Prefijo común de todos los temas MQTT (ver docs/mqtt-topics.md).
    mqtt_prefijo: str = "bajoterra/01"
    # Identificador del cliente MQTT del backend; debe ser único en el broker.
    mqtt_client_id: str = "bajoterra-backend"
    # Nivel de detalle de los logs: DEBUG, INFO, WARNING o ERROR.
    nivel_log: str = "INFO"
    # Cuántas lecturas se guardan en memoria por serie (zona o depósito).
    max_lecturas: int = 720
    # Cuántos comandos se guardan en memoria.
    max_comandos: int = 200
    # Segundos sin lecturas a partir de los cuales un dato se considera desactualizado.
    umbral_desactualizado_s: int = 15
    # Segundos de vida por defecto de un comando antes de caducar.
    ttl_comando_s: int = 30

    # Construye los ajustes leyendo las variables de entorno.
    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> "Ajustes":
        # Si no se pasa un diccionario se usan las variables reales del sistema.
        entorno = os.environ if entorno is None else entorno
        # Normaliza el nivel de log a mayúsculas.
        nivel = entorno.get("NIVEL_LOG", "INFO").upper()
        # Solo se aceptan los cuatro niveles conocidos.
        if nivel not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            # Error claro si el valor no es uno de ellos.
            raise ValueError(f"NIVEL_LOG debe ser DEBUG, INFO, WARNING o ERROR, pero vale {nivel!r}")
        # Crea el objeto con cada valor de entorno (o su valor por defecto).
        return cls(
            mqtt_host=entorno.get("MQTT_HOST", "localhost"),
            mqtt_puerto=_entero(entorno, "MQTT_PUERTO", 1883, 1, 65535),
            mqtt_usuario=entorno.get("MQTT_USER", ""),
            mqtt_clave=entorno.get("MQTT_PASSWORD", ""),
            mqtt_prefijo=entorno.get("MQTT_PREFIJO", "bajoterra/01").strip("/"),
            mqtt_client_id=entorno.get("MQTT_CLIENT_ID", "bajoterra-backend"),
            nivel_log=nivel,
            max_lecturas=_entero(entorno, "MAX_LECTURAS_POR_SERIE", 720, 10, 100000),
            max_comandos=_entero(entorno, "MAX_COMANDOS", 200, 10, 10000),
            umbral_desactualizado_s=_entero(entorno, "UMBRAL_DESACTUALIZADO_S", 15, 1, 3600),
            ttl_comando_s=_entero(entorno, "TTL_COMANDO_S", 30, 5, 300),
        )
