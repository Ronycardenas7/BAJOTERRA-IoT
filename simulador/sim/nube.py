"""Simulador en modo NUBE (opción A, docs/tiempo-real.md): envía las lecturas SIMULADAS directo a Supabase por HTTPS,
igual que lo hará el ESP32, y ejecuta las órdenes que lleguen desde la web.

Uso (desde la carpeta simulador/, con el entorno virtual del proyecto):
    python -m sim.nube

Lee la configuración de variables de entorno o del archivo simulador/secretos_nube.conf (plantilla: secretos_nube.ejemplo.conf):
    SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SIM_CLAVE_DISPOSITIVO, SIM_INTERVALO_S (por defecto 10 s).
No necesita broker MQTT ni backend.
"""

# Anotaciones de tipo modernas en cualquier versión de Python.
from __future__ import annotations

# json: convertir diccionarios a texto JSON y viceversa.
import json
# logging: mensajes de diagnóstico con hora.
import logging
# os: variables de entorno.
import os
# signal: detenerse con orden ante Ctrl+C o la señal de terminación.
import signal
# threading.Event: señal de parada que además sirve de espera interrumpible.
import threading
# time.monotonic: reloj que no retrocede (para los modelos y los intervalos).
import time
# urllib: cliente HTTP de la biblioteca estándar (no se instala nada extra).
import urllib.error
import urllib.request
# uuid: identificador único de cada mensaje.
import uuid
# datetime/timedelta: corregir la hora con el desfase del reloj del PC.
from datetime import datetime, timedelta
# Path: rutas de archivos compatibles con Windows y Linux.
from pathlib import Path

# Modelos físicos de las zonas y del depósito (los mismos del modo MQTT).
from sim.modelos import PERFILES, DepositoSimulado, ZonaSimulada
# Fechas en UTC.
from sim.tiempo import a_iso, ahora_utc

# Logger de este módulo.
registro = logging.getLogger("sim.nube")
# Carpeta raíz del proyecto (simulador/sim/nube.py -> sube dos niveles).
RAIZ = Path(__file__).resolve().parent.parent.parent
# Cada cuánto se preguntan las órdenes pendientes (segundos).
INTERVALO_ORDENES_S = 2.0
# Cada cuánto se vuelve a medir el desfase del reloj del PC (segundos).
INTERVALO_RELOJ_S = 600.0
# Desfase a partir del cual se avisa que el reloj del PC está mal (segundos).
AVISO_DESFASE_S = 30.0


# Error devuelto por Supabase (por ejemplo, una clave inválida o un dato fuera de rango).
class ErrorSupabase(Exception):
    pass


def leer_env(ruta: Path) -> dict[str, str]:
    """Lee un archivo CLAVE=valor; ignora comentarios y líneas vacías. Si no existe, devuelve un diccionario vacío."""
    # Resultado.
    valores: dict[str, str] = {}
    # Sin archivo, nada que leer.
    if not ruta.is_file():
        return valores
    # Recorre cada línea.
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        # Quita espacios.
        linea = linea.strip()
        # Salta comentarios y líneas sin "=".
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        # Divide en la primera "=".
        clave, valor = linea.split("=", 1)
        # Guarda el par.
        valores[clave.strip()] = valor.strip()
    # Devuelve lo leído.
    return valores


class ClienteSupabase:
    """Llama a las funciones (RPC) de Supabase por HTTPS con la clave publicable del proyecto."""

    def __init__(self, url: str, clave_publicable: str, tiempo_espera_s: float = 10.0) -> None:
        # Dirección base de las funciones: https://<proyecto>.supabase.co/rest/v1/rpc/
        self._base = url.rstrip("/") + "/rest/v1/rpc/"
        # Encabezados: la clave publicable va en "apikey" (no en Authorization, porque no es un JWT).
        self._encabezados = {"apikey": clave_publicable, "Content-Type": "application/json", "Accept": "application/json"}
        # Tiempo máximo de espera por petición.
        self._espera = tiempo_espera_s

    def rpc(self, funcion: str, datos: dict):
        """Ejecuta una función de la base de datos y devuelve su respuesta ya convertida desde JSON."""
        # Prepara la petición POST con el cuerpo en JSON (UTF-8).
        peticion = urllib.request.Request(
            self._base + funcion, data=json.dumps(datos).encode("utf-8"), headers=self._encabezados, method="POST"
        )
        # Intenta enviarla.
        try:
            # Abre la conexión HTTPS (verifica el certificado del servidor).
            with urllib.request.urlopen(peticion, timeout=self._espera) as respuesta:
                # Lee y convierte la respuesta.
                cuerpo = respuesta.read().decode("utf-8")
                # Algunas funciones no devuelven nada.
                return json.loads(cuerpo) if cuerpo else None
        # Supabase respondió con un error (400, 401, 403...): se extrae su mensaje legible.
        except urllib.error.HTTPError as error:
            # Lee el cuerpo del error.
            texto = error.read().decode("utf-8", errors="replace")
            # PostgREST responde {"message": "..."}; si no es JSON se usa el texto tal cual.
            try:
                mensaje = json.loads(texto).get("message", texto)
            except ValueError:
                mensaje = texto
            # Lanza un error propio con el código HTTP.
            raise ErrorSupabase(f"HTTP {error.code}: {mensaje}") from None


class SimuladorNube:
    """Mantiene los modelos de las 3 zonas y el depósito, envía lecturas y atiende órdenes."""

    def __init__(self, cliente: ClienteSupabase, clave_dispositivo: str, intervalo_s: float, semilla: int | None,
                 bomba_max_s: float, manual_s: float) -> None:
        # Cliente HTTPS.
        self._cliente = cliente
        # Clave propia del dispositivo "simulador" (creada con privado.crear_dispositivo en Supabase).
        self._clave = clave_dispositivo
        # Segundos entre lecturas.
        self._intervalo = intervalo_s
        # Reloj monotónico inicial.
        ahora = time.monotonic()
        # Una zona simulada por perfil (árida, húmeda, selvática), cada una con su semilla.
        self._zonas = {
            nombre: ZonaSimulada(perfil, bomba_max_s, manual_s, None if semilla is None else semilla + i, ahora)
            for i, (nombre, perfil) in enumerate(PERFILES.items())
        }
        # Depósito principal simulado.
        self._deposito = DepositoSimulado(None if semilla is None else semilla + len(PERFILES))
        # Señal de parada.
        self.parar = threading.Event()
        # Diferencia entre la hora del servidor y la del PC (se mide al iniciar).
        self._desfase = timedelta(0)

    def medir_desfase(self) -> None:
        """Compara la hora del PC con la de Supabase y guarda la diferencia (corrige relojes mal configurados)."""
        # Intenta pedir la hora del servidor.
        try:
            # Hora local antes y después de la petición (se usa el punto medio para descontar la demora de la red).
            antes = ahora_utc()
            texto = self._cliente.rpc("hora_servidor", {})
            despues = ahora_utc()
        # Si falla, se conserva el desfase anterior.
        except (ErrorSupabase, urllib.error.URLError, TimeoutError, OSError) as error:
            registro.warning("no se pudo leer la hora del servidor: %s", error)
            return
        # Convierte la respuesta (texto ISO con zona horaria) a fecha.
        servidor = datetime.fromisoformat(texto)
        # Desfase = hora del servidor - hora del PC en el punto medio.
        self._desfase = servidor - (antes + (despues - antes) / 2)
        # Avisa si el reloj del PC está notablemente mal.
        segundos = self._desfase.total_seconds()
        if abs(segundos) > AVISO_DESFASE_S:
            registro.warning("el reloj de este PC está desfasado %+.0f s respecto del servidor; se corrige automáticamente", -segundos)

    def ahora(self) -> datetime:
        """Hora UTC corregida con el desfase medido."""
        # Hora del PC más la corrección.
        return ahora_utc() + self._desfase

    def _enviar(self, carga: dict) -> None:
        """Envía una lectura; un fallo se registra pero no detiene el simulador."""
        # Intenta enviar.
        try:
            # Llama a registrar_lectura con la clave del simulador.
            respuesta = self._cliente.rpc("registrar_lectura", {"p_clave": self._clave, "p_lectura": carga})
            # Muestra el resultado en modo depuración.
            registro.debug("lectura %s: %s", carga.get("zona", carga.get("deposito")), respuesta)
        # Error de Supabase (dato rechazado, clave inválida...).
        except ErrorSupabase as error:
            # Lo informa.
            registro.error("Supabase rechazó la lectura de %s: %s", carga.get("zona", carga.get("deposito")), error)
        # Error de red (sin internet, DNS, tiempo agotado...).
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            # Lo informa; se reintenta en el siguiente ciclo.
            registro.warning("sin conexión con Supabase: %s", error)

    def enviar_lecturas(self) -> None:
        """Avanza los modelos y envía una lectura por zona y una del depósito."""
        # Reloj actual.
        ahora = time.monotonic()
        # Una lectura por zona.
        for nombre, zona in self._zonas.items():
            # Avanza la física simulada.
            zona.paso(ahora)
            # Arma el mensaje con el contrato del proyecto; "zona" indica a qué zona pertenece.
            carga = {
                "id_mensaje": str(uuid.uuid4()),
                "dispositivo": f"sim-zona-{nombre}",
                "zona": nombre,
                "origen": "simulado",
                "medido_en": a_iso(self.ahora()),
                "calidad": "buena",
                **zona.instantanea(),
            }
            # Envía.
            self._enviar(carga)
        # Avanza el depósito.
        self._deposito.paso()
        # Lectura del depósito.
        self._enviar({
            "id_mensaje": str(uuid.uuid4()),
            "dispositivo": "sim-deposito-principal",
            "deposito": "principal",
            "origen": "simulado",
            "medido_en": a_iso(self.ahora()),
            "calidad": "buena",
            **self._deposito.instantanea(),
        })

    def atender_ordenes(self) -> None:
        """Pregunta las órdenes pendientes, las aplica al modelo y confirma el resultado."""
        # Pide las órdenes pendientes.
        try:
            pendientes = self._cliente.rpc("comandos_pendientes", {"p_clave": self._clave}) or []
        # Si falla, se reintenta en el siguiente ciclo.
        except (ErrorSupabase, urllib.error.URLError, TimeoutError, OSError) as error:
            registro.warning("no se pudieron leer las órdenes: %s", error)
            return
        # Procesa cada orden.
        for orden in pendientes:
            # Zona simulada destino.
            zona = self._zonas.get(orden.get("zona"))
            # Aplica la orden al modelo (revisa caducidad y repetidos) o la rechaza si la zona no existe.
            resultado, detalle = (
                zona.aplicar_comando(orden, self.ahora(), time.monotonic()) if zona else ("rechazado", "zona desconocida")
            )
            # Informa en pantalla.
            registro.info("orden %s %s=%s -> %s", orden.get("zona"), orden.get("actuador"), orden.get("estado_solicitado"), resultado)
            # Confirma en Supabase (origen "simulado": no hay hardware).
            try:
                self._cliente.rpc("confirmar_comando", {
                    "p_clave": self._clave, "p_id_comando": orden["id_comando"],
                    "p_resultado": resultado, "p_origen": "simulado", "p_detalle": detalle,
                })
            # Si la confirmación falla, la orden vencerá sola y la web lo mostrará como "sin confirmación".
            except (ErrorSupabase, urllib.error.URLError, TimeoutError, OSError) as error:
                registro.warning("no se pudo confirmar la orden %s: %s", orden.get("id_comando"), error)

    def ejecutar(self) -> None:
        """Bucle principal: lecturas cada "intervalo" segundos y órdenes cada 2 s, hasta que se pida parar."""
        # Momento del próximo envío de lecturas (inmediato al comenzar).
        proximo_envio = 0.0
        # Momento de la próxima medición del reloj (inmediata al comenzar).
        proximo_reloj = 0.0
        # Repite hasta recibir la señal de parada.
        while not self.parar.is_set():
            # Reloj actual.
            ahora = time.monotonic()
            # ¿Toca medir el desfase del reloj?
            if ahora >= proximo_reloj:
                # Mide y programa la siguiente medición.
                self.medir_desfase()
                proximo_reloj = ahora + INTERVALO_RELOJ_S
            # ¿Toca enviar lecturas?
            if ahora >= proximo_envio:
                # Envía y programa el siguiente envío.
                self.enviar_lecturas()
                proximo_envio = ahora + self._intervalo
            # Atiende órdenes en cada vuelta.
            self.atender_ordenes()
            # Espera 2 s (o sale antes si llega la señal de parada).
            self.parar.wait(INTERVALO_ORDENES_S)


def main() -> int:
    """Lee la configuración, valida que esté completa y ejecuta el simulador hasta Ctrl+C."""
    # Formato de los mensajes en pantalla.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Configuración: archivo simulador/secretos_nube.conf (ignorado por Git); el entorno real tiene prioridad.
    entorno = {**leer_env(RAIZ / "simulador" / "secretos_nube.conf"), **os.environ}
    # Datos obligatorios.
    url = entorno.get("SUPABASE_URL", "")
    publicable = entorno.get("SUPABASE_PUBLISHABLE_KEY", "")
    clave = entorno.get("SIM_CLAVE_DISPOSITIVO", "")
    # Si falta alguno, explica qué hacer y termina.
    if not (url and publicable and clave):
        registro.error("Faltan SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY o SIM_CLAVE_DISPOSITIVO. Copia simulador/secretos_nube.ejemplo.conf como simulador/secretos_nube.conf y complétalo.")
        return 1
    # Semilla opcional para resultados reproducibles.
    semilla_texto = entorno.get("SIM_SEMILLA", "")
    # Crea el simulador.
    simulador = SimuladorNube(
        ClienteSupabase(url, publicable),
        clave,
        intervalo_s=max(2.0, float(entorno.get("SIM_INTERVALO_S", "10"))),
        semilla=int(semilla_texto) if semilla_texto else None,
        bomba_max_s=float(entorno.get("SIM_BOMBA_MAX_S", "60")),
        manual_s=float(entorno.get("SIM_MANUAL_S", "120")),
    )
    # Ctrl+C o SIGTERM activan la parada ordenada.
    for senal in (signal.SIGINT, signal.SIGTERM):
        signal.signal(senal, lambda *_: simulador.parar.set())
    # Mensaje inicial (sin mostrar claves).
    registro.info("Simulador en modo nube: enviando datos SIMULADOS a %s cada %.0f s. Ctrl+C para detener.", url, simulador._intervalo)
    # Ejecuta.
    simulador.ejecutar()
    # Despedida.
    registro.info("Simulador detenido.")
    return 0


# Permite ejecutarlo con "python -m sim.nube".
if __name__ == "__main__":
    raise SystemExit(main())
