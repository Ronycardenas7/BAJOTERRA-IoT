# Piezas compartidas por las pruebas: reloj falso, publicador falso, cliente MQTT falso y generadores de mensajes.
# Ninguna prueba necesita un broker real ni Internet.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# json convierte los mensajes de prueba a bytes, como llegarían por MQTT.
import json
# uuid genera identificadores únicos de mensaje.
import uuid
# datetime/timedelta/timezone para controlar el tiempo en las pruebas.
from datetime import datetime, timedelta, timezone

# pytest da fixtures (preparación reutilizable).
import pytest

# Error que simula la caída del broker.
from app.domain.errores import BrokerNoDisponible

# Instante fijo usado como "ahora" en las pruebas.
INICIO = datetime(2026, 10, 26, 16, 0, 0, tzinfo=timezone.utc)


# Reloj controlable: devuelve siempre el mismo instante hasta que la prueba lo avanza.
class RelojFalso:
    # Empieza en el instante indicado.
    def __init__(self, inicio: datetime = INICIO) -> None:
        # Instante actual del reloj falso.
        self.ahora = inicio

    # Al llamar al objeto como función devuelve el instante actual.
    def __call__(self) -> datetime:
        # Devuelve el instante guardado.
        return self.ahora

    # Avanza el reloj la cantidad de segundos indicada.
    def avanzar(self, segundos: float) -> None:
        # Suma los segundos al instante actual.
        self.ahora += timedelta(seconds=segundos)


# Publicador falso: guarda los comandos en una lista en vez de enviarlos.
class PublicadorFalso:
    # Constructor sin parámetros.
    def __init__(self) -> None:
        # Comandos "enviados".
        self.enviados = []
        # Si es True, simula que el broker está caído.
        self.fallar = False

    # Imita el método enviar del publicador real.
    def enviar(self, comando) -> None:
        # Si se pidió fallar, lanza el mismo error que el cliente real.
        if self.fallar:
            # Simula broker caído.
            raise BrokerNoDisponible("sin conexión con el broker MQTT")
        # Si no, solo guarda el comando.
        self.enviados.append(comando)


# Cliente MQTT falso con la misma "forma" que el real: suscribir, publicar y conectado.
class ClienteMqttFalso:
    # Constructor sin parámetros.
    def __init__(self) -> None:
        # Suscripciones registradas: lista de (filtro, qos, manejador).
        self.suscripciones = []
        # Mensajes publicados: lista de (tema, carga, qos, retain).
        self.publicados = []
        # Indica si "hay conexión".
        self.conectado = True

    # Imita suscribir: solo guarda la suscripción.
    def suscribir(self, filtro, qos, manejador) -> None:
        # Guarda la tupla.
        self.suscripciones.append((filtro, qos, manejador))

    # Imita publicar: falla si no hay conexión, si no guarda el mensaje.
    def publicar(self, tema, carga, qos=1, retain=False) -> None:
        # Sin conexión, igual que el cliente real.
        if not self.conectado:
            # Simula broker caído.
            raise BrokerNoDisponible("sin conexión con el broker MQTT")
        # Guarda el mensaje publicado.
        self.publicados.append((tema, carga, qos, retain))

    # Busca el manejador registrado para un filtro concreto.
    def manejador(self, filtro: str):
        # Recorre las suscripciones buscando el filtro exacto.
        for f, _, manejador in self.suscripciones:
            # Si coincide, lo devuelve.
            if f == filtro:
                # Manejador encontrado.
                return manejador
        # Si no hay ninguno, la prueba debe fallar con un mensaje claro.
        raise AssertionError(f"no hay suscripción para {filtro}")


# Fixture: reloj falso nuevo para cada prueba.
@pytest.fixture
def reloj() -> RelojFalso:
    # Devuelve un reloj en el instante inicial.
    return RelojFalso()


# Fixture: publicador falso nuevo para cada prueba.
@pytest.fixture
def publicador() -> PublicadorFalso:
    # Devuelve un publicador vacío.
    return PublicadorFalso()


# Construye un mensaje de telemetría de zona válido (como diccionario); "cambios" permite modificarlo.
def carga_zona(**cambios) -> dict:
    # Mensaje base que cumple el contrato.
    base = {
        "id_mensaje": str(uuid.uuid4()),
        "dispositivo": "sim-zona-arida",
        "origen": "simulado",
        "medido_en": "2026-10-26T16:00:00Z",
        "calidad": "buena",
        "mediciones": {"temperatura": 19.5, "humedad_ambiente": 70.0, "humedad_sustrato": 60.0, "luz": 12000.0},
        "actuadores": {"bomba": "apagado", "ventilador": "apagado", "luces": "apagado"},
        "modo": "automatico",
    }
    # Aplica los cambios pedidos por la prueba.
    base.update(cambios)
    # Devuelve el mensaje.
    return base


# Construye un mensaje de telemetría de depósito válido.
def carga_deposito(**cambios) -> dict:
    # Mensaje base que cumple el contrato.
    base = {
        "id_mensaje": str(uuid.uuid4()),
        "dispositivo": "sim-deposito",
        "origen": "simulado",
        "medido_en": "2026-10-26T16:00:00Z",
        "calidad": "buena",
        "mediciones": {"conductividad_ec": 1.8, "nivel_agua": None, "agua_disponible": True},
    }
    # Aplica los cambios pedidos por la prueba.
    base.update(cambios)
    # Devuelve el mensaje.
    return base


# Convierte un diccionario a bytes JSON, como llega un mensaje MQTT real.
def a_bytes(carga: dict) -> bytes:
    # Serializa a JSON y codifica en UTF-8.
    return json.dumps(carga).encode("utf-8")
