# Cliente del broker MQTT (infraestructura). Envuelve la biblioteca paho-mqtt y esconde sus detalles.
# Se encarga de: conectar, reconectar solo, re-suscribirse tras cada reconexión y publicar mensajes JSON.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# json convierte diccionarios a texto JSON.
import json
# logging escribe mensajes de diagnóstico.
import logging
# threading da hilos, cerrojos y eventos.
import threading
# Callable describe "una función que se puede llamar".
from collections.abc import Callable

# paho-mqtt: biblioteca cliente MQTT.
import paho.mqtt.client as mqtt

# Error que se lanza cuando no se puede publicar.
from app.domain.errores import BrokerNoDisponible

# Logger de este módulo.
registro = logging.getLogger(__name__)

# Tipo de un manejador de mensajes: recibe (tema, contenido en bytes).
Manejador = Callable[[str, bytes], None]


# Cliente MQTT con reconexión automática.
class ClienteMqtt:
    # Crea el cliente (todavía sin conectar).
    def __init__(self, host: str, puerto: int, usuario: str, clave: str, client_id: str) -> None:
        # Dirección del broker.
        self._host = host
        # Puerto del broker.
        self._puerto = puerto
        # Cliente paho en modo de callbacks versión 2; clean_session=True evita que el broker guarde mensajes
        # para este cliente mientras está desconectado (no queremos reprocesar cosas viejas).
        self._cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=True)
        # Si se configuró usuario, se usa autenticación por usuario y contraseña.
        if usuario:
            # Registra las credenciales en el cliente (no se escriben en los logs).
            self._cliente.username_pw_set(usuario, clave)
        # Si se pierde la conexión, reintenta esperando entre 1 y 30 segundos (con espera creciente).
        self._cliente.reconnect_delay_set(min_delay=1, max_delay=30)
        # Función que se ejecuta al conectarse.
        self._cliente.on_connect = self._al_conectar
        # Función que se ejecuta al desconectarse.
        self._cliente.on_disconnect = self._al_desconectar
        # Función que se ejecuta al recibir un mensaje.
        self._cliente.on_message = self._al_recibir
        # Lista de suscripciones: (filtro de temas, QoS, manejador).
        self._suscripciones: list[tuple[str, int, Manejador]] = []
        # Cerrojo para proteger la lista de suscripciones entre hilos.
        self._cerrojo = threading.Lock()
        # Señal que está activa mientras hay conexión con el broker.
        self._conectado = threading.Event()

    # Indica si hay conexión activa con el broker.
    @property
    def conectado(self) -> bool:
        # Event.is_set() es True mientras la señal está activa.
        return self._conectado.is_set()

    # Registra una suscripción. Se aplica al conectar y se repite tras cada reconexión.
    def suscribir(self, filtro: str, qos: int, manejador: Manejador) -> None:
        # Toma el cerrojo mientras se modifica la lista.
        with self._cerrojo:
            # Guarda la suscripción para aplicarla (o re-aplicarla) al conectar.
            self._suscripciones.append((filtro, qos, manejador))
        # Si ya hay conexión, se suscribe de inmediato.
        if self.conectado:
            # Pide al broker la suscripción.
            self._cliente.subscribe(filtro, qos)

    # Publica un diccionario como JSON. Lanza BrokerNoDisponible si no hay conexión.
    def publicar(self, tema: str, carga: dict, qos: int = 1, retain: bool = False) -> None:
        # Sin conexión no se publica: así las órdenes no quedan en cola para enviarse más tarde sin control.
        if not self.conectado:
            # Error 503 hacia la API.
            raise BrokerNoDisponible("sin conexión con el broker MQTT")
        # Convierte el diccionario a JSON compacto en UTF-8.
        texto = json.dumps(carga, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        # Entrega el mensaje al cliente paho.
        resultado = self._cliente.publish(tema, texto, qos=qos, retain=retain)
        # paho informa éxito con MQTT_ERR_SUCCESS; cualquier otro código es un fallo.
        if resultado.rc != mqtt.MQTT_ERR_SUCCESS:
            # Error 503 hacia la API, con el código para diagnóstico.
            raise BrokerNoDisponible(f"no se pudo publicar en el broker (código {resultado.rc})")

    # Inicia la conexión en segundo plano. No bloquea y reintenta sola si el broker aún no está listo.
    def iniciar(self) -> None:
        # Registra el intento en el log.
        registro.info("Conectando al broker MQTT en %s:%s", self._host, self._puerto)
        # connect_async no bloquea ni falla si el broker aún no responde.
        self._cliente.connect_async(self._host, self._puerto, keepalive=30)
        # Arranca el hilo de red de paho (conecta, reconecta y recibe mensajes).
        self._cliente.loop_start()

    # Detiene la conexión de forma ordenada.
    def detener(self) -> None:
        # Cierra la conexión con el broker.
        self._cliente.disconnect()
        # Detiene el hilo de red.
        self._cliente.loop_stop()

    # Callback de paho: ocurre al conectar (o reconectar).
    def _al_conectar(self, cliente, userdata, flags, codigo, propiedades) -> None:
        # Si el broker rechazó la conexión (por ejemplo, clave incorrecta), lo deja claro en el log.
        if codigo.is_failure:
            # No se imprime la contraseña, solo el motivo.
            registro.error("El broker MQTT rechazó la conexión: %s", codigo)
            # No sigue.
            return
        # Deja constancia de la conexión.
        registro.info("Conectado al broker MQTT")
        # Toma el cerrojo para leer la lista de suscripciones.
        with self._cerrojo:
            # Copia la lista para recorrerla sin riesgo.
            pendientes = list(self._suscripciones)
        # Aplica cada suscripción (necesario tras cada reconexión porque la sesión es limpia).
        for filtro, qos, _ in pendientes:
            # Pide al broker la suscripción.
            cliente.subscribe(filtro, qos)
        # Marca que hay conexión activa.
        self._conectado.set()

    # Callback de paho: ocurre al perder la conexión.
    def _al_desconectar(self, cliente, userdata, banderas, codigo, propiedades) -> None:
        # Marca que ya no hay conexión.
        self._conectado.clear()
        # Avisa en el log; paho reintentará solo.
        registro.warning("Desconectado del broker MQTT (%s); se reintentará automáticamente", codigo)

    # Callback de paho: ocurre al llegar un mensaje.
    def _al_recibir(self, cliente, userdata, mensaje) -> None:
        # Toma el cerrojo para copiar la lista de suscripciones.
        with self._cerrojo:
            # Copia para recorrer sin riesgo.
            suscripciones = list(self._suscripciones)
        # Recorre las suscripciones buscando las que coincidan con el tema recibido.
        for filtro, _, manejador in suscripciones:
            # topic_matches_sub entiende los comodines "+" y "#".
            if mqtt.topic_matches_sub(filtro, mensaje.topic):
                # Intenta procesar el mensaje.
                try:
                    # Entrega tema y contenido al manejador.
                    manejador(mensaje.topic, bytes(mensaje.payload))
                # Cualquier error inesperado se registra, pero no se deja morir el hilo de red.
                except Exception:
                    # exception() incluye el detalle del error para depurar.
                    registro.exception("Error inesperado procesando un mensaje en %s", mensaje.topic)
