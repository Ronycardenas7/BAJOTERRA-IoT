# Manejadores de mensajes MQTT entrantes: adaptan el mensaje (tema + bytes) a llamadas de los servicios.
# Regla de robustez: un mensaje malo se registra y se descarta; NUNCA debe tumbar el proceso.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# functools.wraps conserva el nombre de la función decorada.
import functools
# logging escribe mensajes de diagnóstico.
import logging

# Listas de zonas y depósitos válidos.
from app.domain.constantes import DEPOSITOS, ZONAS
# Errores del dominio.
from app.domain.errores import ErrorDominio, MensajeInvalido
# Funciones que validan cada tipo de mensaje.
from app.schemas import mensajes
# Servicios que reciben los datos validados.
from app.services.comandos_service import ServicioComandos
from app.services.telemetria_service import ServicioTelemetria
# Constructor y lector de temas.
from app.mqtt.temas import Temas

# Logger de este módulo.
registro = logging.getLogger(__name__)


# Decorador: ejecuta el manejador y, si el mensaje es inválido o falla una regla del dominio, solo lo registra.
def _descartar_si_invalido(funcion):
    # Conserva nombre y documentación de la función original.
    @functools.wraps(funcion)
    # Función envoltorio con la misma firma que los manejadores.
    def envoltorio(self, tema: str, carga: bytes) -> None:
        # Intenta ejecutar el manejador real.
        try:
            # Llama al manejador con el tema y el contenido.
            funcion(self, tema, carga)
        # Captura cualquier error esperado del dominio (mensaje inválido, comando desconocido...).
        except ErrorDominio as error:
            # Lo deja como advertencia con el tema, para poder diagnosticar un dispositivo que envía datos malos.
            registro.warning("Mensaje descartado en %s: %s", tema, error.mensaje)
    # Devuelve el envoltorio en lugar de la función original.
    return envoltorio


# Agrupa los manejadores y los registra en el cliente MQTT.
class ManejadorMensajes:
    # Recibe los servicios y el lector de temas.
    def __init__(self, telemetria: ServicioTelemetria, comandos: ServicioComandos, temas: Temas) -> None:
        # Servicio de telemetría.
        self._telemetria = telemetria
        # Servicio de comandos.
        self._comandos = comandos
        # Lector de temas.
        self._temas = temas

    # Suscribe cada manejador a su filtro de temas con la calidad de servicio (QoS) del contrato.
    def registrar(self, cliente) -> None:
        # Telemetría de zonas: QoS 0 (si se pierde una lectura, llega la siguiente).
        cliente.suscribir(self._temas.filtro_telemetria_zonas(), 0, self.telemetria_zona)
        # Confirmaciones de comandos: QoS 1 (no deben perderse).
        cliente.suscribir(self._temas.filtro_confirmaciones_zonas(), 1, self.confirmacion)
        # Telemetría de depósitos: QoS 0.
        cliente.suscribir(self._temas.filtro_telemetria_depositos(), 0, self.telemetria_deposito)
        # Estado de conexión de dispositivos: QoS 1.
        cliente.suscribir(self._temas.filtro_estado_dispositivos(), 1, self.estado_dispositivo)

    # Extrae el identificador del tema y comprueba que el recurso y el tipo sean los esperados.
    def _identificador(self, tema: str, recurso: str, tipo: str) -> str:
        # Separa el tema en (recurso, identificador, tipo).
        partes = self._temas.separar(tema)
        # Si el formato no coincide, se rechaza.
        if partes is None or partes[0] != recurso or partes[2] != tipo:
            # Mensaje claro.
            raise MensajeInvalido(f"el tema no tiene el formato esperado para {recurso}/{tipo}")
        # Devuelve el identificador (zona, depósito o dispositivo).
        return partes[1]

    # Maneja la telemetría de una zona.
    @_descartar_si_invalido
    def telemetria_zona(self, tema: str, carga: bytes) -> None:
        # La zona viene en el tema.
        zona = self._identificador(tema, "zonas", "telemetria")
        # Solo se aceptan zonas conocidas.
        if zona not in ZONAS:
            # Se rechaza el mensaje.
            raise MensajeInvalido(f"zona desconocida en el tema: {zona!r}")
        # Valida el contenido del mensaje.
        datos = mensajes.validar_telemetria_zona(mensajes.cargar_json(carga))
        # Entrega los datos validados al servicio.
        self._telemetria.registrar_zona(zona, datos)

    # Maneja la telemetría de un depósito.
    @_descartar_si_invalido
    def telemetria_deposito(self, tema: str, carga: bytes) -> None:
        # El depósito viene en el tema.
        deposito = self._identificador(tema, "depositos", "telemetria")
        # Solo se aceptan depósitos conocidos.
        if deposito not in DEPOSITOS:
            # Se rechaza el mensaje.
            raise MensajeInvalido(f"depósito desconocido en el tema: {deposito!r}")
        # Valida el contenido del mensaje.
        datos = mensajes.validar_telemetria_deposito(mensajes.cargar_json(carga))
        # Entrega los datos validados al servicio.
        self._telemetria.registrar_deposito(deposito, datos)

    # Maneja el estado de conexión de un dispositivo.
    @_descartar_si_invalido
    def estado_dispositivo(self, tema: str, carga: bytes) -> None:
        # El identificador del dispositivo viene en el tema y debe tener formato válido.
        dispositivo = mensajes.validar_id_dispositivo(self._identificador(tema, "dispositivos", "estado"))
        # Valida el contenido del mensaje.
        datos = mensajes.validar_estado_dispositivo(mensajes.cargar_json(carga))
        # Entrega los datos validados al servicio.
        self._telemetria.registrar_estado(dispositivo, datos)

    # Maneja la confirmación de un comando.
    @_descartar_si_invalido
    def confirmacion(self, tema: str, carga: bytes) -> None:
        # Comprueba que el tema sea el de confirmaciones de una zona (el valor de la zona no se usa después).
        self._identificador(tema, "zonas", "confirmaciones")
        # Valida el contenido del mensaje.
        datos = mensajes.validar_confirmacion(mensajes.cargar_json(carga))
        # Entrega los datos validados al servicio.
        self._comandos.registrar_confirmacion(datos)
