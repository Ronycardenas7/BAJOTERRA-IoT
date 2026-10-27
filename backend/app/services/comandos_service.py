# Servicio de comandos: solicita órdenes a los actuadores y registra su ciclo de vida.
# Regla clave: una orden pendiente NO equivale a un actuador encendido. El estado real lo informa la telemetría.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# logging escribe mensajes de diagnóstico.
import logging
# uuid genera identificadores únicos para cada comando.
import uuid
# Callable describe "una función que se puede llamar".
from collections.abc import Callable
# dataclasses.replace crea una copia de un comando con algunos campos cambiados.
from dataclasses import replace
# datetime es el tipo del instante actual; timedelta permite sumar segundos.
from datetime import datetime, timedelta
# Protocol define una interfaz por "forma".
from typing import Protocol

# Valores permitidos del dominio.
from app.domain.constantes import ACTUADORES, ESTADOS_ACTUADOR, ZONAS
# Errores del dominio.
from app.domain.errores import BrokerNoDisponible, ComandoNoEncontrado, DatosInvalidos, ZonaDesconocida
# Entidad Comando.
from app.domain.modelos import Comando
# Utilidades de tiempo.
from app.domain.tiempo import ahora_utc
# Contrato del repositorio de comandos.
from app.repositories.base import RepositorioComandos

# Logger de este módulo.
registro = logging.getLogger(__name__)

# Estados finales: una vez alcanzados, el comando ya no cambia.
ESTADOS_FINALES = ("ejecutado", "rechazado", "caducado", "duplicado", "fallido_envio")
# Vida mínima y máxima permitidas para un comando, en segundos.
TTL_MIN_S = 5
TTL_MAX_S = 300


# Contrato del componente que entrega el comando al mundo exterior (hoy, MQTT).
class PublicadorComandos(Protocol):
    # Envía el comando; lanza BrokerNoDisponible si no se pudo entregar.
    def enviar(self, comando: Comando) -> None: ...


# Caso de uso: solicitar comandos y registrar sus confirmaciones.
class ServicioComandos:
    # Recibe sus dependencias desde afuera para poder probarlo sin broker.
    def __init__(
        self,
        repositorio: RepositorioComandos,
        publicador: PublicadorComandos,
        ttl_defecto_s: int,
        reloj: Callable[[], datetime] = ahora_utc,
        generar_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        # Dónde se guardan los comandos.
        self._repositorio = repositorio
        # Cómo se entregan los comandos.
        self._publicador = publicador
        # Vida por defecto de un comando, en segundos.
        self._ttl_defecto = ttl_defecto_s
        # Función que devuelve la hora actual (se reemplaza en las pruebas).
        self._reloj = reloj
        # Función que genera ids únicos (se reemplaza en las pruebas).
        self._generar_id = generar_id

    # Solicita una orden: valida, registra, entrega al broker y devuelve el comando.
    def solicitar(self, zona: str, actuador: str, estado: str, ttl_s: int | None = None) -> Comando:
        # La zona debe existir.
        if zona not in ZONAS:
            # Error 404 con las zonas válidas.
            raise ZonaDesconocida(f"zona desconocida: {zona!r}; use una de {list(ZONAS)}")
        # El actuador debe ser conocido.
        if actuador not in ACTUADORES:
            # Error 400 con los valores válidos.
            raise DatosInvalidos(f"'actuador' debe ser uno de {list(ACTUADORES)}")
        # El estado pedido debe ser conocido.
        if estado not in ESTADOS_ACTUADOR:
            # Error 400 con los valores válidos.
            raise DatosInvalidos(f"'estado' debe ser uno de {list(ESTADOS_ACTUADOR)}")
        # Si no se indicó vida, usa la de por defecto.
        ttl = self._ttl_defecto if ttl_s is None else ttl_s
        # La vida debe ser un entero (bool no cuenta) dentro del rango permitido.
        if isinstance(ttl, bool) or not isinstance(ttl, int) or not TTL_MIN_S <= ttl <= TTL_MAX_S:
            # Error 400 con el rango válido.
            raise DatosInvalidos(f"'ttl_segundos' debe ser un entero entre {TTL_MIN_S} y {TTL_MAX_S}")
        # Instante de la solicitud.
        ahora = self._reloj()
        # Crea el comando. Se marca "enviado" justo antes de entregarlo al broker (ver explicación abajo).
        comando = Comando(
            id_comando=self._generar_id(),
            zona=zona,
            actuador=actuador,
            estado_solicitado=estado,
            estado="enviado",
            solicitado_en=ahora,
            caduca_en=ahora + timedelta(seconds=ttl),
            enviado_en=ahora,
        )
        # Se guarda ANTES de publicar: si la confirmación llega muy rápido, el comando ya existe.
        self._repositorio.guardar(comando)
        # Intenta entregar el comando al broker.
        try:
            # Publica la orden en el tema de comandos de la zona.
            self._publicador.enviar(comando)
        # Si el broker no está disponible, la orden NO salió.
        except BrokerNoDisponible as error:
            # Registra el fallo en el comando para dejar rastro (y borra enviado_en porque no salió).
            self._repositorio.guardar(replace(comando, estado="fallido_envio", enviado_en=None, detalle=error.mensaje))
            # Informa a quien llamó (la API responderá 503).
            raise
        # Devuelve el comando tal como quedó registrado.
        return comando

    # Registra la confirmación que envió un dispositivo. "datos" ya fue validado.
    def registrar_confirmacion(self, datos: dict) -> Comando:
        # Busca el comando al que responde la confirmación.
        comando = self._repositorio.obtener(datos["id_comando"])
        # Si no existe (por ejemplo, el backend se reinició), se informa.
        if comando is None:
            # La capa MQTT registrará una advertencia y descartará el mensaje.
            raise ComandoNoEncontrado(f"confirmación de un comando desconocido: {datos['id_comando']}")
        # Si el comando ya tiene resultado final, se ignora la confirmación repetida (el primer resultado manda).
        if comando.estado in ESTADOS_FINALES:
            # Deja una nota de depuración.
            registro.debug("Confirmación repetida ignorada para el comando %s", comando.id_comando)
            # Devuelve el comando sin cambios.
            return comando
        # Crea la versión confirmada del comando; el estado toma el nombre del resultado informado.
        confirmado = replace(
            comando,
            estado=datos["resultado"],
            confirmado_en=datos["confirmado_en"],
            dispositivo=datos["dispositivo"],
            origen_confirmacion=datos["origen"],
            detalle=datos["detalle"],
        )
        # Guarda la versión confirmada.
        self._repositorio.guardar(confirmado)
        # Devuelve el comando actualizado.
        return confirmado

    # Devuelve un comando por id o lanza ComandoNoEncontrado.
    def obtener(self, id_comando: str) -> Comando:
        # Busca el comando.
        comando = self._repositorio.obtener(id_comando)
        # Si no existe, error 404.
        if comando is None:
            # Mensaje claro con el id buscado.
            raise ComandoNoEncontrado(f"no existe el comando {id_comando!r}")
        # Devuelve el comando encontrado.
        return comando

    # Devuelve los últimos comandos de una zona.
    def listar_zona(self, zona: str, limite: int) -> list[Comando]:
        # La zona debe existir.
        if zona not in ZONAS:
            # Error 404 con las zonas válidas.
            raise ZonaDesconocida(f"zona desconocida: {zona!r}; use una de {list(ZONAS)}")
        # Delega la consulta al repositorio.
        return self._repositorio.listar_zona(zona, limite)
