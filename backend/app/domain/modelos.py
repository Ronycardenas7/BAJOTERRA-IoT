# Entidades del dominio. Son clases de solo datos (sin lógica de base de datos ni de MQTT).

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# dataclass crea clases de datos; "replace" crea una copia con algunos campos cambiados.
from dataclasses import dataclass
# datetime es el tipo de los instantes de tiempo.
from datetime import datetime

# a_iso convierte fechas a texto UTC para la respuesta JSON.
from .tiempo import a_iso


# Convierte una fecha opcional a texto ISO; si no hay fecha devuelve None (dato ausente, nunca un valor inventado).
def _iso_o_nulo(momento: datetime | None) -> str | None:
    # Si hay fecha la convierte; si no, devuelve None.
    return a_iso(momento) if momento is not None else None


# frozen=True hace la clase inmutable: una lectura ya registrada no se puede alterar por accidente.
@dataclass(frozen=True)
class LecturaZona:
    # Zona a la que pertenece la lectura (viene del tema MQTT).
    zona: str
    # Identificador del dispositivo que midió.
    dispositivo: str
    # "real" o "simulado".
    origen: str
    # Identificador único del mensaje (UUID); sirve para detectar duplicados.
    id_mensaje: str
    # Instante en que el dispositivo midió (UTC).
    medido_en: datetime
    # Instante en que el backend recibió el mensaje (UTC).
    recibido_en: datetime
    # Calidad declarada por el dispositivo.
    calidad: str
    # Mediciones por nombre; un valor None significa "dato ausente".
    mediciones: dict
    # Estado REPORTADO de los actuadores (no es lo mismo que una orden pendiente).
    actuadores: dict
    # Modo de la zona (automático o manual) o None si no se informó.
    modo: str | None

    # Convierte la lectura a un diccionario listo para JSON.
    def a_dict(self) -> dict:
        # Devuelve cada campo; las fechas se convierten a texto UTC.
        return {
            "zona": self.zona,
            "dispositivo": self.dispositivo,
            "origen": self.origen,
            "id_mensaje": self.id_mensaje,
            "medido_en": a_iso(self.medido_en),
            "recibido_en": a_iso(self.recibido_en),
            "calidad": self.calidad,
            "mediciones": dict(self.mediciones),
            "actuadores": dict(self.actuadores),
            "modo": self.modo,
        }


# Lectura de un depósito de agua (conductividad, disponibilidad de agua...).
@dataclass(frozen=True)
class LecturaDeposito:
    # Depósito al que pertenece la lectura (viene del tema MQTT).
    deposito: str
    # Identificador del dispositivo que midió.
    dispositivo: str
    # "real" o "simulado".
    origen: str
    # Identificador único del mensaje (UUID).
    id_mensaje: str
    # Instante de la medición (UTC).
    medido_en: datetime
    # Instante de recepción en el backend (UTC).
    recibido_en: datetime
    # Calidad declarada por el dispositivo.
    calidad: str
    # Mediciones por nombre; None significa "dato ausente".
    mediciones: dict

    # Convierte la lectura a un diccionario listo para JSON.
    def a_dict(self) -> dict:
        # Devuelve cada campo; las fechas se convierten a texto UTC.
        return {
            "deposito": self.deposito,
            "dispositivo": self.dispositivo,
            "origen": self.origen,
            "id_mensaje": self.id_mensaje,
            "medido_en": a_iso(self.medido_en),
            "recibido_en": a_iso(self.recibido_en),
            "calidad": self.calidad,
            "mediciones": dict(self.mediciones),
        }


# Estado de conexión de un dispositivo, según lo que publicó en el tema "estado".
@dataclass(frozen=True)
class EstadoDispositivo:
    # Identificador del dispositivo.
    dispositivo: str
    # "en_linea" o "desconectado".
    estado: str
    # "real" o "simulado".
    origen: str
    # Instante en que el backend recibió este estado (UTC).
    actualizado_en: datetime

    # Convierte el estado a un diccionario listo para JSON.
    def a_dict(self) -> dict:
        # Devuelve cada campo; la fecha se convierte a texto UTC.
        return {
            "dispositivo": self.dispositivo,
            "estado": self.estado,
            "origen": self.origen,
            "actualizado_en": a_iso(self.actualizado_en),
        }


# Orden enviada a un actuador. Su ciclo de vida se registra por etapas:
# solicitado -> enviado -> (ejecutado | rechazado | caducado | duplicado), o fallido_envio si no salió.
@dataclass(frozen=True)
class Comando:
    # Identificador único del comando (UUID).
    id_comando: str
    # Zona destino.
    zona: str
    # Actuador destino ("bomba", "ventilador" o "luces").
    actuador: str
    # Estado que se pide ("encendido" o "apagado"). Pedirlo NO significa que el actuador ya lo tenga.
    estado_solicitado: str
    # Etapa actual del comando.
    estado: str
    # Instante en que se solicitó (UTC).
    solicitado_en: datetime
    # Instante después del cual el comando ya no debe ejecutarse (UTC).
    caduca_en: datetime
    # Instante en que se publicó en el broker (None si aún no salió).
    enviado_en: datetime | None = None
    # Instante en que llegó la confirmación del dispositivo (None si aún no llega).
    confirmado_en: datetime | None = None
    # Dispositivo que confirmó (None hasta que confirme).
    dispositivo: str | None = None
    # "real" o "simulado" según quien confirmó (None hasta que confirme).
    origen_confirmacion: str | None = None
    # Texto opcional que explica el resultado (por ejemplo, por qué se rechazó).
    detalle: str | None = None

    # Convierte el comando a un diccionario listo para JSON.
    def a_dict(self) -> dict:
        # Devuelve cada campo; las fechas se convierten a texto UTC (o None si faltan).
        return {
            "id_comando": self.id_comando,
            "zona": self.zona,
            "actuador": self.actuador,
            "estado_solicitado": self.estado_solicitado,
            "estado": self.estado,
            "solicitado_en": a_iso(self.solicitado_en),
            "caduca_en": a_iso(self.caduca_en),
            "enviado_en": _iso_o_nulo(self.enviado_en),
            "confirmado_en": _iso_o_nulo(self.confirmado_en),
            "dispositivo": self.dispositivo,
            "origen_confirmacion": self.origen_confirmacion,
            "detalle": self.detalle,
        }
