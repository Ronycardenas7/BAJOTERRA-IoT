# Contratos (interfaces) de los repositorios. Los servicios dependen de ESTOS contratos, no de una base concreta.
# Hoy hay una implementación en memoria; cuando se integre Supabase se agregará otra sin tocar los servicios.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# Protocol define una interfaz por "forma": cualquier clase con estos métodos la cumple.
from typing import Protocol

# Entidades que manejan los repositorios.
from app.domain.modelos import Comando, EstadoDispositivo, LecturaDeposito, LecturaZona


# Contrato para guardar y consultar lecturas de zonas y depósitos.
class RepositorioTelemetria(Protocol):
    # Guarda una lectura de zona; devuelve False si el id_mensaje ya estaba (duplicado).
    def guardar_zona(self, lectura: LecturaZona) -> bool: ...

    # Guarda una lectura de depósito; devuelve False si el id_mensaje ya estaba (duplicado).
    def guardar_deposito(self, lectura: LecturaDeposito) -> bool: ...

    # Devuelve la última lectura de una zona, o None si aún no hay.
    def ultima_zona(self, zona: str) -> LecturaZona | None: ...

    # Devuelve las últimas lecturas de una zona, de la más antigua a la más reciente.
    def historial_zona(self, zona: str, limite: int) -> list[LecturaZona]: ...

    # Devuelve la última lectura de un depósito, o None si aún no hay.
    def ultima_deposito(self, deposito: str) -> LecturaDeposito | None: ...


# Contrato para guardar y consultar el estado de conexión de los dispositivos.
class RepositorioDispositivos(Protocol):
    # Guarda (o reemplaza) el estado de un dispositivo.
    def guardar(self, estado: EstadoDispositivo) -> None: ...

    # Devuelve el estado de un dispositivo, o None si nunca informó.
    def obtener(self, dispositivo: str) -> EstadoDispositivo | None: ...


# Contrato para guardar y consultar comandos.
class RepositorioComandos(Protocol):
    # Guarda (o reemplaza) un comando por su id_comando.
    def guardar(self, comando: Comando) -> None: ...

    # Devuelve un comando por id, o None si no existe.
    def obtener(self, id_comando: str) -> Comando | None: ...

    # Devuelve los últimos comandos de una zona, del más reciente al más antiguo.
    def listar_zona(self, zona: str, limite: int) -> list[Comando]: ...
