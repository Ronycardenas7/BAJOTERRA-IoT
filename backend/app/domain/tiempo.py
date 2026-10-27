# Utilidades de tiempo. Todo el sistema trabaja en UTC; la zona horaria solo se aplica al mostrar en la web.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# datetime es la clase de fecha y hora; timezone permite indicar UTC.
from datetime import datetime, timezone


# Devuelve el instante actual en UTC (con zona horaria incluida, no "ingenua").
def ahora_utc() -> datetime:
    # datetime.now(timezone.utc) pide la hora actual ya expresada en UTC.
    return datetime.now(timezone.utc)


# Convierte un datetime a texto ISO 8601 en UTC, por ejemplo "2026-10-26T16:07:00.123Z".
def a_iso(momento: datetime) -> str:
    # Pasa el instante a UTC por si venía en otra zona horaria.
    en_utc = momento.astimezone(timezone.utc)
    # isoformat con milisegundos produce "...+00:00"; se reemplaza por "Z", la forma corta de UTC.
    return en_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")


# Convierte un texto ISO 8601 a datetime en UTC. Exige que el texto incluya zona horaria.
def desde_iso(texto: str) -> datetime:
    # fromisoformat entiende la "Z" final desde Python 3.11; lanza ValueError si el texto es inválido.
    momento = datetime.fromisoformat(texto)
    # Si no trae zona horaria no se sabe a qué hora se refiere: se rechaza.
    if momento.tzinfo is None:
        # El mensaje explica qué falta.
        raise ValueError("la fecha no incluye zona horaria (use UTC, por ejemplo 2026-10-26T16:07:00Z)")
    # Normaliza a UTC para comparar fechas sin confusión.
    return momento.astimezone(timezone.utc)
