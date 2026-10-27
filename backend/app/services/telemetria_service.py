# Servicio de telemetría: reglas de negocio para lecturas y estado de conexión.
# No sabe nada de HTTP ni de MQTT: recibe datos ya validados y usa repositorios por su contrato.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# Callable describe "una función que se puede llamar" (aquí, el reloj).
from collections.abc import Callable
# datetime es el tipo del instante actual.
from datetime import datetime

# Listas de zonas/depósitos y unidades de medida.
from app.domain.constantes import DEPOSITOS, UNIDADES, ZONAS
# Errores del dominio.
from app.domain.errores import ZonaDesconocida
# Entidades del dominio.
from app.domain.modelos import EstadoDispositivo, LecturaDeposito, LecturaZona
# Utilidades de tiempo.
from app.domain.tiempo import a_iso, ahora_utc
# Contratos de los repositorios.
from app.repositories.base import RepositorioDispositivos, RepositorioTelemetria


# Caso de uso: registrar lecturas y armar el resumen que consume la web.
class ServicioTelemetria:
    # Recibe sus dependencias desde afuera (inyección de dependencias): así es fácil probarlo.
    def __init__(
        self,
        telemetria: RepositorioTelemetria,
        dispositivos: RepositorioDispositivos,
        umbral_desactualizado_s: int,
        reloj: Callable[[], datetime] = ahora_utc,
    ) -> None:
        # Repositorio donde se guardan las lecturas.
        self._telemetria = telemetria
        # Repositorio donde se guarda el estado de conexión de los dispositivos.
        self._dispositivos = dispositivos
        # Segundos sin datos a partir de los cuales una lectura se marca como desactualizada.
        self._umbral = umbral_desactualizado_s
        # Función que devuelve la hora actual (se reemplaza en las pruebas).
        self._reloj = reloj

    # Guarda una lectura de zona. "datos" ya fue validado por la capa de esquemas.
    def registrar_zona(self, zona: str, datos: dict) -> bool:
        # Comprueba que la zona exista.
        self._exigir_zona(zona)
        # Crea la entidad agregando la zona y la hora de recepción.
        lectura = LecturaZona(zona=zona, recibido_en=self._reloj(), **datos)
        # Guarda; devuelve False si era un mensaje duplicado.
        return self._telemetria.guardar_zona(lectura)

    # Guarda una lectura de depósito. "datos" ya fue validado.
    def registrar_deposito(self, deposito: str, datos: dict) -> bool:
        # Comprueba que el depósito exista.
        if deposito not in DEPOSITOS:
            # Error claro si no existe.
            raise ZonaDesconocida(f"depósito desconocido: {deposito!r}")
        # Crea la entidad agregando el depósito y la hora de recepción.
        lectura = LecturaDeposito(deposito=deposito, recibido_en=self._reloj(), **datos)
        # Guarda; devuelve False si era un duplicado.
        return self._telemetria.guardar_deposito(lectura)

    # Guarda el estado de conexión que publicó un dispositivo.
    def registrar_estado(self, dispositivo: str, datos: dict) -> None:
        # Crea la entidad con la hora de recepción del backend.
        estado = EstadoDispositivo(
            dispositivo=dispositivo,
            estado=datos["estado"],
            origen=datos["origen"],
            actualizado_en=self._reloj(),
        )
        # Guarda (reemplaza el estado anterior de ese dispositivo).
        self._dispositivos.guardar(estado)

    # Devuelve el historial reciente de una zona como lista de diccionarios.
    def historial_zona(self, zona: str, limite: int) -> list[dict]:
        # Comprueba que la zona exista.
        self._exigir_zona(zona)
        # Convierte cada lectura a diccionario para JSON.
        return [lectura.a_dict() for lectura in self._telemetria.historial_zona(zona, limite)]

    # Arma el resumen completo: última lectura y conexión de cada zona y depósito.
    def resumen(self) -> dict:
        # Una sola lectura del reloj para que todo el resumen sea coherente.
        ahora = self._reloj()
        # Resultado con datos generales.
        return {
            # Instante en que se generó el resumen.
            "generado_en": a_iso(ahora),
            # Umbral usado para marcar datos desactualizados.
            "umbral_desactualizado_s": self._umbral,
            # Unidades para que la web no las repita.
            "unidades": UNIDADES,
            # Una entrada por zona.
            "zonas": {zona: self._entrada_zona(zona, ahora) for zona in ZONAS},
            # Una entrada por depósito.
            "depositos": {dep: self._entrada_deposito(dep, ahora) for dep in DEPOSITOS},
        }

    # Comprueba que una zona exista; si no, lanza ZonaDesconocida.
    def _exigir_zona(self, zona: str) -> None:
        # Compara con la lista de zonas conocidas.
        if zona not in ZONAS:
            # Error claro con las zonas válidas.
            raise ZonaDesconocida(f"zona desconocida: {zona!r}; use una de {list(ZONAS)}")

    # Arma la entrada del resumen para una zona.
    def _entrada_zona(self, zona: str, ahora: datetime) -> dict:
        # Última lectura registrada de la zona (puede no existir).
        lectura = self._telemetria.ultima_zona(zona)
        # Devuelve la lectura (o None) junto con el estado de conexión.
        return {
            "zona": zona,
            "lectura": lectura.a_dict() if lectura else None,
            "conexion": self._conexion(lectura, ahora),
        }

    # Arma la entrada del resumen para un depósito.
    def _entrada_deposito(self, deposito: str, ahora: datetime) -> dict:
        # Última lectura registrada del depósito (puede no existir).
        lectura = self._telemetria.ultima_deposito(deposito)
        # Devuelve la lectura (o None) junto con el estado de conexión.
        return {
            "deposito": deposito,
            "lectura": lectura.a_dict() if lectura else None,
            "conexion": self._conexion(lectura, ahora),
        }

    # Calcula el estado de conexión a partir de la última lectura y el último estado del dispositivo.
    def _conexion(self, lectura: LecturaZona | LecturaDeposito | None, ahora: datetime) -> dict:
        # Sin lecturas no se sabe nada: se declara desconocido y desactualizado.
        if lectura is None:
            # Valores nulos en vez de inventar datos.
            return {
                "estado": "desconocido",
                "dispositivo": None,
                "segundos_desde_ultima_lectura": None,
                "desactualizada": True,
            }
        # Segundos desde que el backend recibió la última lectura (usa el reloj del backend, no el del dispositivo).
        edad = max((ahora - lectura.recibido_en).total_seconds(), 0.0)
        # Último estado informado por el dispositivo que midió.
        estado_dispositivo = self._dispositivos.obtener(lectura.dispositivo)
        # Devuelve el estado de conexión completo.
        return {
            "estado": estado_dispositivo.estado if estado_dispositivo else "desconocido",
            "dispositivo": lectura.dispositivo,
            "segundos_desde_ultima_lectura": round(edad, 1),
            "desactualizada": edad > self._umbral,
        }
