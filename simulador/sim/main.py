# Programa principal del simulador: crea los tres dispositivos y publica telemetría cada cierto tiempo.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# logging escribe mensajes de diagnóstico.
import logging
# signal permite reaccionar a Ctrl+C y a la orden de parada de Docker.
import signal
# threading.Event se usa como "señal de parada" que además sirve de temporizador.
import threading

# Ajustes y dispositivos del simulador.
from sim.config import Ajustes
from sim.dispositivos import DispositivoDeposito, DispositivoZona

# Logger de este módulo.
registro = logging.getLogger("sim")


# Ejecuta el simulador hasta que se pida detenerlo. Devuelve el código de salida del programa.
def ejecutar() -> int:
    # Lee la configuración (falla con un mensaje claro si hay un valor inválido).
    ajustes = Ajustes.desde_entorno()
    # Configura el formato de los logs.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Si hay semilla, cada dispositivo usa una distinta (semilla, semilla+1...) para que no sean idénticos.
    base = ajustes.semilla
    # Crea los dispositivos: las tres zonas (árida, húmeda y selvática) y un depósito.
    dispositivos = [
        DispositivoZona(ajustes, "arida", None if base is None else base),
        DispositivoZona(ajustes, "humeda", None if base is None else base + 1),
        DispositivoZona(ajustes, "selvatica", None if base is None else base + 2),
        DispositivoDeposito(ajustes, "principal", None if base is None else base + 3),
    ]
    # Señal de parada: se activa con Ctrl+C o con SIGTERM (docker stop).
    parar = threading.Event()
    # Al recibir cualquiera de las dos señales, activa la parada.
    for senal in (signal.SIGINT, signal.SIGTERM):
        # El lambda ignora los argumentos que entrega signal y solo activa el evento.
        signal.signal(senal, lambda *_: parar.set())
    # Deja claro desde el inicio que los datos NO son reales.
    registro.warning("SIMULADOR ACTIVO: todos los datos publicados son SIMULADOS (origen=simulado)")
    # Inicia la conexión de cada dispositivo.
    for dispositivo in dispositivos:
        # Conexión en segundo plano.
        dispositivo.iniciar()
    # Bucle principal: espera "intervalo" segundos (o hasta que se pida parar) y publica.
    while not parar.wait(ajustes.intervalo_s):
        # Cada dispositivo publica su lectura.
        for dispositivo in dispositivos:
            # Publica telemetría.
            dispositivo.publicar_telemetria()
    # Llegó la orden de parada: cierra cada dispositivo avisando que se desconecta.
    registro.info("Deteniendo el simulador...")
    # Cierre ordenado.
    for dispositivo in dispositivos:
        # Publica "desconectado" y cierra.
        dispositivo.detener()
    # Código de salida 0 = terminó bien.
    return 0
