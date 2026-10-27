# Dispositivos MQTT simulados. Cada dispositivo es un cliente MQTT independiente, como lo sería cada ESP32:
# - publica su estado de conexión (con "última voluntad" por si se cae),
# - publica telemetría periódica,
# - (solo las zonas) recibe comandos y responde con una confirmación.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# json convierte diccionarios a texto JSON y viceversa.
import json
# logging escribe mensajes de diagnóstico.
import logging
# threading da hilos, cerrojos y eventos.
import threading
# time.monotonic es un reloj que nunca retrocede (ideal para medir duraciones).
import time
# uuid genera identificadores únicos de mensaje.
import uuid
# Callable describe "una función que se puede llamar".
from collections.abc import Callable

# paho-mqtt: biblioteca cliente MQTT.
import paho.mqtt.client as mqtt

# Ajustes y modelos del simulador.
from sim.config import Ajustes
from sim.modelos import PERFILES, DepositoSimulado, ZonaSimulada
# Utilidades de tiempo.
from sim.tiempo import a_iso, ahora_utc

# Logger de este módulo.
registro = logging.getLogger(__name__)

# Origen que lleva TODO mensaje del simulador.
ORIGEN = "simulado"


# Cliente MQTT de un dispositivo, con estado de conexión y última voluntad.
class ClienteDispositivo:
    # Prepara el cliente (todavía sin conectar).
    def __init__(
        self,
        ajustes: Ajustes,
        dispositivo: str,
        tema_estado: str,
        suscripciones: dict[str, int] | None = None,
        al_mensaje: Callable[[str, bytes], None] | None = None,
    ) -> None:
        # Datos de conexión.
        self._host = ajustes.mqtt_host
        self._puerto = ajustes.mqtt_puerto
        # Tema donde se publica el estado de conexión.
        self._tema_estado = tema_estado
        # Temas a los que se suscribe (tema -> QoS).
        self._suscripciones = suscripciones or {}
        # Función a la que se entregan los mensajes recibidos.
        self._al_mensaje = al_mensaje
        # El id del cliente es el id del dispositivo (debe ser único en el broker).
        self._cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=dispositivo, clean_session=True)
        # Autenticación si hay usuario configurado.
        if ajustes.mqtt_usuario:
            # Registra las credenciales (no se imprimen).
            self._cliente.username_pw_set(ajustes.mqtt_usuario, ajustes.mqtt_clave)
        # "Última voluntad": si el dispositivo se cae sin despedirse, el broker publica "desconectado" por él.
        self._cliente.will_set(tema_estado, self._carga_estado("desconectado"), qos=1, retain=True)
        # Reintenta la conexión esperando entre 1 y 30 segundos.
        self._cliente.reconnect_delay_set(min_delay=1, max_delay=30)
        # Registra los callbacks.
        self._cliente.on_connect = self._al_conectar
        self._cliente.on_disconnect = self._al_desconectar
        self._cliente.on_message = self._al_recibir
        # Señal activa mientras hay conexión.
        self._conectado = threading.Event()
        # Nombre para los logs.
        self._nombre = dispositivo

    # Construye el contenido JSON del mensaje de estado.
    @staticmethod
    def _carga_estado(estado: str) -> bytes:
        # El contrato exige estado y origen; la hora la agrega el backend al recibirlo.
        return json.dumps({"estado": estado, "origen": ORIGEN}).encode("utf-8")

    # Indica si hay conexión con el broker.
    @property
    def conectado(self) -> bool:
        # Event.is_set() es True mientras la señal está activa.
        return self._conectado.is_set()

    # Inicia la conexión en segundo plano.
    def iniciar(self) -> None:
        # connect_async no bloquea ni falla si el broker aún no está listo.
        self._cliente.connect_async(self._host, self._puerto, keepalive=30)
        # Arranca el hilo de red (conecta, reconecta y recibe).
        self._cliente.loop_start()

    # Publica un diccionario como JSON. Devuelve False si no hay conexión (la telemetría perdida no se reenvía).
    def publicar(self, tema: str, carga: dict, qos: int = 0, retain: bool = False) -> bool:
        # Sin conexión no se publica.
        if not self.conectado:
            # Informa que no se envió.
            return False
        # Convierte a JSON compacto y lo entrega a paho.
        resultado = self._cliente.publish(tema, json.dumps(carga, separators=(",", ":")), qos=qos, retain=retain)
        # True si paho aceptó el mensaje.
        return resultado.rc == mqtt.MQTT_ERR_SUCCESS

    # Cierra de forma ordenada: avisa "desconectado" antes de irse (la última voluntad solo actúa en caídas).
    def detener(self) -> None:
        # Si hay conexión, publica el estado desconectado y espera a que salga.
        if self.conectado:
            # Publica el estado con retain para que quede registrado en el broker.
            info = self._cliente.publish(self._tema_estado, self._carga_estado("desconectado"), qos=1, retain=True)
            # Espera hasta 2 segundos a que el mensaje salga.
            info.wait_for_publish(timeout=2)
        # Cierra la conexión.
        self._cliente.disconnect()
        # Detiene el hilo de red.
        self._cliente.loop_stop()

    # Callback de paho: al conectar.
    def _al_conectar(self, cliente, userdata, flags, codigo, propiedades) -> None:
        # Si el broker rechazó la conexión, lo deja claro (sin imprimir la contraseña).
        if codigo.is_failure:
            # Registra el motivo.
            registro.error("[%s] el broker rechazó la conexión: %s", self._nombre, codigo)
            # No sigue.
            return
        # Se suscribe a los temas necesarios (también tras cada reconexión, porque la sesión es limpia).
        for tema, qos in self._suscripciones.items():
            # Pide la suscripción.
            cliente.subscribe(tema, qos)
        # Anuncia que está en línea (retain: cualquiera que se conecte después lo sabrá).
        cliente.publish(self._tema_estado, self._carga_estado("en_linea"), qos=1, retain=True)
        # Marca la conexión como activa.
        self._conectado.set()
        # Deja constancia.
        registro.info("[%s] conectado al broker", self._nombre)

    # Callback de paho: al desconectar.
    def _al_desconectar(self, cliente, userdata, banderas, codigo, propiedades) -> None:
        # Marca la conexión como inactiva.
        self._conectado.clear()
        # Avisa en el log; paho reintentará solo.
        registro.warning("[%s] desconectado del broker (%s)", self._nombre, codigo)

    # Callback de paho: al recibir un mensaje.
    def _al_recibir(self, cliente, userdata, mensaje) -> None:
        # Si nadie escucha mensajes, no hay nada que hacer.
        if self._al_mensaje is None:
            # Termina.
            return
        # Intenta procesar el mensaje.
        try:
            # Entrega tema y contenido.
            self._al_mensaje(mensaje.topic, bytes(mensaje.payload))
        # Un error al procesar no debe matar el hilo de red.
        except Exception:
            # exception() incluye el detalle del error.
            registro.exception("[%s] error procesando un mensaje", self._nombre)


# Dispositivo simulado de una zona (árida, húmeda o selvática).
class DispositivoZona:
    # Prepara el dispositivo. Los relojes se pueden reemplazar en las pruebas.
    def __init__(
        self,
        ajustes: Ajustes,
        zona: str,
        semilla: int | None = None,
        reloj_mono: Callable[[], float] = time.monotonic,
        reloj_utc: Callable = ahora_utc,
    ) -> None:
        # Nombre de la zona.
        self.zona = zona
        # Identificador del dispositivo (formato aceptado por el backend).
        self.dispositivo = f"sim-zona-{zona}"
        # Relojes.
        self._mono = reloj_mono
        self._utc = reloj_utc
        # Modelo físico de la zona.
        self._modelo = ZonaSimulada(PERFILES[zona], ajustes.bomba_max_s, ajustes.manual_s, semilla, reloj_mono())
        # Cerrojo: el hilo principal (telemetría) y el hilo MQTT (comandos) tocan el mismo modelo.
        self._cerrojo = threading.Lock()
        # Temas del contrato.
        prefijo = ajustes.mqtt_prefijo
        self._tema_telemetria = f"{prefijo}/zonas/{zona}/telemetria"
        self._tema_comandos = f"{prefijo}/zonas/{zona}/comandos"
        self._tema_confirmaciones = f"{prefijo}/zonas/{zona}/confirmaciones"
        # Cliente MQTT: escucha los comandos de SU zona (QoS 1).
        self._cliente = ClienteDispositivo(
            ajustes,
            self.dispositivo,
            f"{prefijo}/dispositivos/{self.dispositivo}/estado",
            {self._tema_comandos: 1},
            self._al_comando,
        )

    # Inicia la conexión.
    def iniciar(self) -> None:
        # Delega en el cliente.
        self._cliente.iniciar()

    # Cierra la conexión.
    def detener(self) -> None:
        # Delega en el cliente.
        self._cliente.detener()

    # Avanza el modelo y publica una lectura de telemetría.
    def publicar_telemetria(self) -> None:
        # Con el cerrojo tomado, avanza el modelo y toma la foto del estado.
        with self._cerrojo:
            # Avanza la simulación hasta ahora.
            self._modelo.paso(self._mono())
            # Foto del estado.
            foto = self._modelo.instantanea()
        # Arma el mensaje según el contrato.
        carga = {
            "id_mensaje": str(uuid.uuid4()),
            "dispositivo": self.dispositivo,
            "origen": ORIGEN,
            "medido_en": a_iso(self._utc()),
            "calidad": "buena",
            **foto,
        }
        # Publica con QoS 0 (si se pierde una lectura, llega la siguiente).
        if not self._cliente.publicar(self._tema_telemetria, carga, qos=0):
            # Deja una nota de depuración si no hubo conexión.
            registro.debug("[%s] telemetría no enviada (sin conexión)", self.dispositivo)

    # Procesa un comando recibido y publica la confirmación.
    def _al_comando(self, tema: str, crudo: bytes) -> None:
        # Intenta leer el JSON.
        try:
            # Convierte los bytes a diccionario.
            carga = json.loads(crudo.decode("utf-8"))
        # Si no es JSON válido, no hay id al cual responder: se descarta.
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Advierte en el log.
            registro.warning("[%s] comando ilegible descartado", self.dispositivo)
            # Termina.
            return
        # Un comando debe ser un objeto JSON.
        if not isinstance(carga, dict):
            # Advierte en el log.
            registro.warning("[%s] comando con formato inesperado descartado", self.dispositivo)
            # Termina.
            return
        # Con el cerrojo tomado, aplica el comando al modelo.
        with self._cerrojo:
            # Devuelve el resultado y un detalle.
            resultado, detalle = self._modelo.aplicar_comando(carga, self._utc(), self._mono())
        # Sin un id válido no se puede confirmar.
        id_comando = carga.get("id_comando")
        # Debe ser texto.
        if not isinstance(id_comando, str):
            # Termina sin confirmar.
            return
        # Confirmación según el contrato.
        confirmacion = {
            "id_comando": id_comando,
            "dispositivo": self.dispositivo,
            "origen": ORIGEN,
            "resultado": resultado,
            "confirmado_en": a_iso(self._utc()),
            "detalle": detalle,
        }
        # Publica con QoS 1 (la confirmación no debe perderse).
        self._cliente.publicar(self._tema_confirmaciones, confirmacion, qos=1)
        # Deja constancia en el log.
        registro.info("[%s] comando %s -> %s", self.dispositivo, id_comando, resultado)


# Dispositivo simulado del depósito de agua.
class DispositivoDeposito:
    # Prepara el dispositivo.
    def __init__(self, ajustes: Ajustes, deposito: str = "principal", semilla: int | None = None) -> None:
        # Nombre del depósito.
        self.deposito = deposito
        # Identificador del dispositivo.
        self.dispositivo = f"sim-deposito-{deposito}"
        # Modelo físico del depósito.
        self._modelo = DepositoSimulado(semilla)
        # Tema de telemetría del depósito.
        self._tema_telemetria = f"{ajustes.mqtt_prefijo}/depositos/{deposito}/telemetria"
        # Cliente MQTT: no recibe comandos.
        self._cliente = ClienteDispositivo(
            ajustes, self.dispositivo, f"{ajustes.mqtt_prefijo}/dispositivos/{self.dispositivo}/estado"
        )

    # Inicia la conexión.
    def iniciar(self) -> None:
        # Delega en el cliente.
        self._cliente.iniciar()

    # Cierra la conexión.
    def detener(self) -> None:
        # Delega en el cliente.
        self._cliente.detener()

    # Avanza el modelo y publica una lectura de telemetría.
    def publicar_telemetria(self) -> None:
        # Avanza la simulación.
        self._modelo.paso()
        # Arma el mensaje según el contrato.
        carga = {
            "id_mensaje": str(uuid.uuid4()),
            "dispositivo": self.dispositivo,
            "origen": ORIGEN,
            "medido_en": a_iso(ahora_utc()),
            "calidad": "buena",
            **self._modelo.instantanea(),
        }
        # Publica con QoS 0.
        if not self._cliente.publicar(self._tema_telemetria, carga, qos=0):
            # Deja una nota de depuración si no hubo conexión.
            registro.debug("[%s] telemetría no enviada (sin conexión)", self.dispositivo)
