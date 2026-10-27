# Utilidades de tiempo del simulador. Todo en UTC, igual que el backend.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# datetime es la clase de fecha y hora; timezone permite indicar UTC.
from datetime import datetime, timezone


# Devuelve el instante actual en UTC.
def ahora_utc() -> datetime:
    # datetime.now(timezone.utc) pide la hora ya expresada en UTC.
    return datetime.now(timezone.utc)


# Convierte un datetime a texto ISO 8601 en UTC, por ejemplo "2026-10-26T16:07:00.123Z".
def a_iso(momento: datetime) -> str:
    # Pasa a UTC y escribe con milisegundos; "+00:00" se reemplaza por la forma corta "Z".
    return momento.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# Convierte un texto ISO 8601 a datetime en UTC. Exige zona horaria.
def desde_iso(texto: str) -> datetime:
    # fromisoformat entiende la "Z" final; lanza ValueError si el texto es inválido.
    momento = datetime.fromisoformat(texto)
    # Sin zona horaria no se sabe a qué hora se refiere: se rechaza.
    if momento.tzinfo is None:
        # Mensaje claro.
        raise ValueError("la fecha no incluye zona horaria")
    # Normaliza a UTC.
    return momento.astimezone(timezone.utc)
