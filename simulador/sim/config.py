# Configuración del simulador: lee variables de entorno y las valida al arrancar.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# os da acceso a las variables de entorno.
import os
# Mapping es el tipo de un diccionario de solo lectura (como os.environ).
from collections.abc import Mapping
# dataclass crea una clase de solo datos.
from dataclasses import dataclass


# Lee una variable de entorno numérica (entera o decimal) dentro de un rango.
def _numero(entorno: Mapping[str, str], nombre: str, defecto: float, minimo: float, maximo: float) -> float:
    # Busca la variable; si no existe usa el valor por defecto.
    crudo = entorno.get(nombre, str(defecto))
    # Intenta convertir a número decimal.
    try:
        # float() lanza ValueError si el texto no es un número.
        valor = float(crudo)
    # Captura el texto no numérico.
    except ValueError:
        # Mensaje que nombra la variable y su valor.
        raise ValueError(f"La variable {nombre} debe ser un número, pero vale {crudo!r}") from None
    # Comprueba el rango permitido.
    if not minimo <= valor <= maximo:
        # Mensaje con el rango válido.
        raise ValueError(f"La variable {nombre} debe estar entre {minimo} y {maximo}, pero vale {valor}")
    # Devuelve el número validado.
    return valor


# frozen=True: los ajustes no cambian mientras el programa corre.
@dataclass(frozen=True)
class Ajustes:
    # Nombre o IP del broker MQTT (en Docker es "mosquitto").
    mqtt_host: str = "localhost"
    # Puerto del broker.
    mqtt_puerto: int = 1883
    # Usuario MQTT; vacío = sin autenticación (solo pruebas locales).
    mqtt_usuario: str = ""
    # Contraseña MQTT. Nunca se imprime.
    mqtt_clave: str = ""
    # Prefijo común de los temas (debe coincidir con el del backend).
    mqtt_prefijo: str = "bajoterra/01"
    # Segundos entre cada publicación de telemetría.
    intervalo_s: float = 5.0
    # Semilla del generador aleatorio; con una semilla fija los datos simulados se repiten igual.
    semilla: int | None = None
    # Límite local de funcionamiento continuo de la bomba, en segundos (seguridad básica del "firmware").
    bomba_max_s: float = 60.0
    # Segundos que dura el modo manual tras recibir una orden, antes de volver al automático.
    manual_s: float = 120.0

    # Construye los ajustes desde las variables de entorno.
    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> "Ajustes":
        # Si no se pasa un diccionario se usan las variables reales del sistema.
        entorno = os.environ if entorno is None else entorno
        # La semilla es opcional: vacía significa "aleatoria".
        semilla_texto = entorno.get("SIM_SEMILLA", "")
        # Crea el objeto con cada valor de entorno (o su valor por defecto).
        return cls(
            mqtt_host=entorno.get("MQTT_HOST", "localhost"),
            mqtt_puerto=int(_numero(entorno, "MQTT_PUERTO", 1883, 1, 65535)),
            mqtt_usuario=entorno.get("MQTT_USER", ""),
            mqtt_clave=entorno.get("MQTT_PASSWORD", ""),
            mqtt_prefijo=entorno.get("MQTT_PREFIJO", "bajoterra/01").strip("/"),
            intervalo_s=_numero(entorno, "SIM_INTERVALO_S", 5.0, 0.2, 3600),
            semilla=int(semilla_texto) if semilla_texto else None,
            bomba_max_s=_numero(entorno, "SIM_BOMBA_MAX_S", 60.0, 1, 3600),
            manual_s=_numero(entorno, "SIM_MANUAL_S", 120.0, 1, 3600),
        )
