# Modelos físicos MUY simples de las zonas y del depósito. No representan la realidad agronómica:
# solo generan datos plausibles para probar el sistema. Los valores objetivo son referencias provisionales.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# math da seno y constantes para las oscilaciones.
import math
# random genera ruido; deque guarda los últimos comandos vistos.
import random
from collections import deque
# dataclass crea clases de datos.
from dataclasses import dataclass
# datetime es el tipo de la hora de un comando.
from datetime import datetime

# Conversión de texto ISO a fecha.
from sim.tiempo import desde_iso

# Segundos que tarda el ambiente en acercarse al valor objetivo (constante de tiempo).
CONSTANTE_TIEMPO_S = 60.0
# Cuánto se seca el sustrato por segundo (puntos porcentuales).
TASA_SECADO = 0.02
# Cuánto sube la humedad del sustrato por segundo con la bomba encendida.
TASA_RIEGO = 0.6
# Duración del ciclo diario simulado (acelerado), en segundos.
CICLO_S = 600.0
# Cuántos grados enfría el ventilador respecto al objetivo.
ENFRIAMIENTO_VENTILADOR = 3.0
# Cuántos puntos de humedad relativa baja el ventilador respecto al objetivo.
SECADO_VENTILADOR = 5.0
# Cuántos ids de comandos se recuerdan para detectar duplicados.
MEMORIA_COMANDOS = 1000
# Cuántos lux agregan las luces LED encendidas a la luz natural de la zona.
LUZ_LED = 1500.0
# Cuántas ppm de CO2 baja el extractor encendido respecto al objetivo (renueva el aire).
REDUCCION_CO2_EXTRACTOR = 200.0
# Histéresis del CO2: el extractor se apaga cuando el CO2 baja este valor (ppm) bajo el máximo.
HISTERESIS_CO2 = 50.0


# Valores de referencia de una zona (provisionales, tomados de la tabla operativa del informe).
@dataclass(frozen=True)
class PerfilZona:
    # Nombre de la zona ("arida", "humeda" o "selvatica").
    nombre: str
    # Temperatura objetivo en °C.
    temperatura: float
    # Humedad relativa objetivo del aire en %.
    humedad_ambiente: float
    # Humedad de sustrato inicial en % relativo.
    humedad_sustrato: float
    # Luz media simulada en lux (inventada; un sensor real necesita calibración).
    luz: float
    # Por debajo de este valor, el control automático enciende la bomba.
    sustrato_bajo: float
    # Por encima de este valor, el control automático apaga la bomba.
    sustrato_alto: float
    # Por encima de esta temperatura, el control automático enciende el ventilador.
    temperatura_max: float
    # Amplitud de la oscilación de temperatura a lo largo del ciclo, en °C.
    amplitud_temp: float
    # Cuánto se seca el sustrato por segundo (puntos porcentuales); más alto = riego más frecuente.
    tasa_secado: float = TASA_SECADO
    # CO2 medio simulado en ppm; None = esta zona no tiene sensor de CO2 (se informa como null).
    co2: float | None = None
    # Por encima de este CO2 (ppm) el control automático enciende el extractor; None = no aplica.
    co2_max: float | None = None
    # Radiación solar media simulada en W/m²; None = esta zona no tiene sensor de radiación.
    radiacion: float | None = None
    # Por debajo de esta luz natural (lux) el control automático enciende las luces LED; 0 = nunca.
    luz_minima: float = 0.0


# Perfiles de las tres zonas de evaluación (valores provisionales e inventados para simular, no agronómicos).
PERFILES = {
    # Zona árida: calor, aire seco, sustrato que se seca y mucha radiación solar (estrés hídrico).
    "arida": PerfilZona(
        "arida", 32.0, 25.0, 18.0, 60000.0, 10.0, 22.0, 35.0, 4.0, tasa_secado=0.03, radiacion=800.0
    ),
    # Zona húmeda: aire muy húmedo, sustrato siempre mojado (riego constante) y luz moderada.
    "humeda": PerfilZona("humeda", 24.0, 85.0, 70.0, 15000.0, 60.0, 75.0, 27.0, 2.0, tasa_secado=0.04),
    # Zona selvática: vegetación densa, CO2 alto, luz difusa baja que se complementa con LED.
    "selvatica": PerfilZona(
        "selvatica", 27.0, 90.0, 65.0, 4000.0, 55.0, 72.0, 30.0, 2.0,
        tasa_secado=0.035, co2=800.0, co2_max=900.0, luz_minima=3800.0,
    ),
}


# Limita un número a un rango.
def _limitar(valor: float, minimo: float, maximo: float) -> float:
    # max/min recortan por abajo y por arriba.
    return max(minimo, min(maximo, valor))


# Zona simulada: temperatura, humedad, luz, CO2, radiación, bomba, ventilador (extractor), luces, modo y comandos.
class ZonaSimulada:
    # Crea la zona. "ahora" es el reloj monotónico (segundos) del momento de creación.
    def __init__(
        self, perfil: PerfilZona, bomba_max_s: float, manual_s: float, semilla: int | None = None, ahora: float = 0.0
    ) -> None:
        # Referencias de la zona.
        self.perfil = perfil
        # Límite local de funcionamiento continuo de la bomba.
        self._bomba_max_s = bomba_max_s
        # Duración del modo manual tras una orden.
        self._manual_s = manual_s
        # Generador aleatorio propio (reproducible si hay semilla).
        self._azar = random.Random(semilla)
        # Valores iniciales = objetivos del perfil.
        self.temperatura = perfil.temperatura
        self.humedad_ambiente = perfil.humedad_ambiente
        self.humedad_sustrato = perfil.humedad_sustrato
        self.luz = perfil.luz
        # Luz natural (sin LED): la medida "luz" suma el aporte de las luces LED cuando están encendidas.
        self._luz_natural = perfil.luz
        # CO2 y radiación: None si la zona no tiene ese sensor.
        self.co2 = perfil.co2
        self.radiacion = perfil.radiacion
        # Actuadores apagados al inicio.
        self.bomba = False
        self.ventilador = False
        self.luces = False
        # Modo inicial: control automático local.
        self.modo = "automatico"
        # Instante (reloj monotónico) en que termina el modo manual.
        self._manual_hasta = 0.0
        # Instante en que se encendió la bomba (None si está apagada).
        self._bomba_desde: float | None = None
        # Instante de la última actualización.
        self._ultimo = ahora
        # Ids de comandos ya procesados, en orden, y como conjunto para consulta rápida.
        self._ids_orden: deque[str] = deque(maxlen=MEMORIA_COMANDOS)
        self._ids_vistos: set[str] = set()

    # Avanza la simulación hasta el instante "ahora" (reloj monotónico, en segundos).
    def paso(self, ahora: float) -> None:
        # Tiempo transcurrido desde el paso anterior (nunca negativo).
        dt = max(0.0, ahora - self._ultimo)
        # Guarda el instante actual para el próximo paso.
        self._ultimo = ahora
        # Si no pasó tiempo no hay nada que actualizar.
        if dt == 0.0:
            # Termina.
            return
        # Fracción del camino hacia el objetivo que se recorre en este paso.
        k = min(1.0, dt / CONSTANTE_TIEMPO_S)
        # Fase del ciclo diario simulado, entre -1 y 1.
        fase = math.sin(2 * math.pi * ahora / CICLO_S)
        # Temperatura objetivo: base + oscilación - enfriamiento si el ventilador está encendido.
        objetivo_t = self.perfil.temperatura + self.perfil.amplitud_temp * fase
        # Aplica el enfriamiento del ventilador.
        if self.ventilador:
            # Resta los grados que enfría.
            objetivo_t -= ENFRIAMIENTO_VENTILADOR
        # La temperatura se acerca al objetivo y recibe un poco de ruido.
        self.temperatura += (objetivo_t - self.temperatura) * k + self._azar.gauss(0, 0.05)
        # Humedad relativa objetivo: base, menos secado si el ventilador está encendido.
        objetivo_h = self.perfil.humedad_ambiente - (SECADO_VENTILADOR if self.ventilador else 0.0)
        # La humedad del aire se acerca al objetivo y recibe un poco de ruido.
        self.humedad_ambiente += (objetivo_h - self.humedad_ambiente) * k + self._azar.gauss(0, 0.2)
        # El sustrato se seca siempre (a la tasa de la zona) y se humedece mientras la bomba está encendida.
        self.humedad_sustrato += (-self.perfil.tasa_secado + (TASA_RIEGO if self.bomba else 0.0)) * dt + self._azar.gauss(0, 0.02)
        # La luz natural oscila ±10 % alrededor de su media, con ruido.
        self._luz_natural = self.perfil.luz * (1 + 0.1 * fase) + self._azar.gauss(0, self.perfil.luz * 0.01)
        # La luz medida suma el aporte de las luces LED si están encendidas.
        self.luz = self._luz_natural + (LUZ_LED if self.luces else 0.0)
        # Si la zona tiene sensor de CO2: sube de noche (respiración), baja de día (fotosíntesis) y con el extractor.
        if self.co2 is not None and self.perfil.co2 is not None:
            # CO2 objetivo: media menos la oscilación del día, menos lo que renueva el extractor.
            objetivo_c = self.perfil.co2 - 150.0 * fase - (REDUCCION_CO2_EXTRACTOR if self.ventilador else 0.0)
            # El CO2 se acerca al objetivo con un poco de ruido.
            self.co2 += (objetivo_c - self.co2) * k + self._azar.gauss(0, 2.0)
            # Rango físico razonable.
            self.co2 = _limitar(self.co2, 250.0, 5000.0)
        # Si la zona tiene sensor de radiación: sigue al sol (más alta en el máximo del ciclo), con ruido.
        if self.radiacion is not None and self.perfil.radiacion is not None:
            # Oscila ±30 % alrededor de la media y nunca es negativa.
            self.radiacion = _limitar(
                self.perfil.radiacion * (1 + 0.3 * fase) + self._azar.gauss(0, self.perfil.radiacion * 0.01), 0.0, 1500.0
            )
        # Mantiene todo dentro de rangos físicos razonables.
        self.temperatura = _limitar(self.temperatura, -40.0, 85.0)
        self.humedad_ambiente = _limitar(self.humedad_ambiente, 0.0, 100.0)
        self.humedad_sustrato = _limitar(self.humedad_sustrato, 0.0, 100.0)
        self.luz = _limitar(self.luz, 0.0, 200000.0)
        # Si terminó el tiempo del modo manual, vuelve al automático.
        if self.modo == "manual" and ahora >= self._manual_hasta:
            # Vuelve al control local automático.
            self.modo = "automatico"
        # En modo automático actúa el control local básico.
        if self.modo == "automatico":
            # Decide si encender o apagar bomba y ventilador.
            self._control_automatico(ahora)
        # Límite de seguridad local: la bomba no puede quedar encendida más de bomba_max_s, sea cual sea el modo.
        if self.bomba and self._bomba_desde is not None and ahora - self._bomba_desde >= self._bomba_max_s:
            # Apaga la bomba por seguridad.
            self._apagar_bomba()

    # Control automático con histéresis (dos umbrales) para no encender y apagar sin parar.
    def _control_automatico(self, ahora: float) -> None:
        # Si el sustrato está seco y la bomba apagada, la enciende.
        if not self.bomba and self.humedad_sustrato < self.perfil.sustrato_bajo:
            # Enciende la bomba.
            self._encender_bomba(ahora)
        # Si el sustrato ya está húmedo y la bomba encendida, la apaga.
        elif self.bomba and self.humedad_sustrato >= self.perfil.sustrato_alto:
            # Apaga la bomba.
            self._apagar_bomba()
        # El extractor se necesita si hace demasiado calor o (con sensor de CO2) si el CO2 supera el máximo.
        demasiado_calor = self.temperatura > self.perfil.temperatura_max
        # Exceso de CO2 (solo si la zona mide CO2 y define un máximo).
        mucho_co2 = self.co2 is not None and self.perfil.co2_max is not None and self.co2 > self.perfil.co2_max
        # Si hace falta y el extractor está apagado, lo enciende.
        if not self.ventilador and (demasiado_calor or mucho_co2):
            # Enciende el extractor.
            self.ventilador = True
        # Si ya bajó 1 °C bajo el máximo y el CO2 también bajó (con histéresis), lo apaga.
        elif self.ventilador and self.temperatura < self.perfil.temperatura_max - 1.0 and not (
            self.co2 is not None and self.perfil.co2_max is not None and self.co2 > self.perfil.co2_max - HISTERESIS_CO2
        ):
            # Apaga el extractor.
            self.ventilador = False
        # Luces LED: se encienden si la luz natural cae bajo el mínimo de la zona (0 = la zona no las necesita).
        if not self.luces and self._luz_natural < self.perfil.luz_minima:
            # Enciende las luces.
            self.luces = True
        # Se apagan cuando la luz natural supera el mínimo con un 5 % de margen.
        elif self.luces and self._luz_natural >= self.perfil.luz_minima * 1.05:
            # Apaga las luces.
            self.luces = False

    # Enciende la bomba y recuerda cuándo, para aplicar el límite de funcionamiento continuo.
    def _encender_bomba(self, ahora: float) -> None:
        # Marca la bomba como encendida.
        self.bomba = True
        # Solo recuerda el instante si no estaba ya encendida.
        if self._bomba_desde is None:
            # Guarda el instante de encendido.
            self._bomba_desde = ahora

    # Apaga la bomba y olvida el instante de encendido.
    def _apagar_bomba(self) -> None:
        # Marca la bomba como apagada.
        self.bomba = False
        # Ya no hay instante de encendido.
        self._bomba_desde = None

    # Procesa un comando recibido. Devuelve (resultado, detalle) para la confirmación.
    def aplicar_comando(self, carga: dict, ahora_utc: datetime, ahora_mono: float) -> tuple[str, str]:
        # El identificador es obligatorio para poder confirmar.
        id_comando = carga.get("id_comando")
        # Debe ser texto no vacío.
        if not isinstance(id_comando, str) or not id_comando:
            # Sin id no se puede identificar el comando.
            return "rechazado", "falta id_comando"
        # Si ya se procesó este id, no se vuelve a ejecutar (los mensajes QoS 1 pueden llegar repetidos).
        if id_comando in self._ids_vistos:
            # Informa duplicado sin hacer nada.
            return "duplicado", "comando ya procesado"
        # Recuerda el id para detectar repeticiones futuras.
        self._recordar(id_comando)
        # El comando debe ser para esta zona.
        if carga.get("zona") != self.perfil.nombre:
            # Rechaza órdenes dirigidas a otra zona.
            return "rechazado", "el comando es de otra zona"
        # Actuador y estado pedidos.
        actuador = carga.get("actuador")
        estado = carga.get("estado_solicitado")
        # Solo existen bomba, ventilador (extractor) y luces.
        if actuador not in ("bomba", "ventilador", "luces"):
            # Rechaza actuadores desconocidos.
            return "rechazado", "actuador desconocido"
        # Solo se puede pedir encendido o apagado.
        if estado not in ("encendido", "apagado"):
            # Rechaza estados desconocidos.
            return "rechazado", "estado solicitado desconocido"
        # Lee la hora de caducidad.
        try:
            # Convierte el texto a fecha UTC.
            caduca = desde_iso(carga["caduca_en"])
        # Captura campo ausente, de tipo incorrecto o con formato inválido.
        except (KeyError, TypeError, ValueError):
            # Sin caducidad válida no se ejecuta (es una regla de seguridad).
            return "rechazado", "caduca_en inválido"
        # Un comando vencido NO se ejecuta (evita acciones tardías, por ejemplo tras una reconexión).
        if ahora_utc > caduca:
            # Informa que llegó tarde.
            return "caducado", "el comando llegó vencido"
        # Indica si la orden es encender.
        encender = estado == "encendido"
        # Aplica la orden a la bomba...
        if actuador == "bomba":
            # ...encendiéndola (y recordando cuándo, para el límite de seguridad)...
            if encender:
                # Enciende la bomba.
                self._encender_bomba(ahora_mono)
            # ...o apagándola.
            else:
                # Apaga la bomba.
                self._apagar_bomba()
        # ...o a las luces LED...
        elif actuador == "luces":
            # Enciende o apaga las luces.
            self.luces = encender
        # ...o al ventilador (extractor).
        else:
            # Enciende o apaga el ventilador.
            self.ventilador = encender
        # Una orden manual pasa la zona a modo manual durante un tiempo.
        self.modo = "manual"
        # Fija cuándo vuelve el modo automático.
        self._manual_hasta = ahora_mono + self._manual_s
        # Aclara que fue ejecutado EN EL SIMULADOR (no en hardware).
        return "ejecutado", "aplicado en el simulador"

    # Recuerda un id de comando, olvidando el más antiguo si la memoria está llena.
    def _recordar(self, id_comando: str) -> None:
        # Si la cola está llena, el id más antiguo saldrá: se quita también del conjunto.
        if len(self._ids_orden) == self._ids_orden.maxlen:
            # Quita del conjunto el id más antiguo.
            self._ids_vistos.discard(self._ids_orden[0])
        # Agrega el nuevo id a la cola y al conjunto.
        self._ids_orden.append(id_comando)
        self._ids_vistos.add(id_comando)

    # Devuelve una foto del estado actual en el formato del contrato MQTT.
    def instantanea(self) -> dict:
        # Mediciones redondeadas a una precisión razonable, actuadores y modo.
        return {
            "mediciones": {
                "temperatura": round(self.temperatura, 2),
                "humedad_ambiente": round(self.humedad_ambiente, 1),
                "humedad_sustrato": round(self.humedad_sustrato, 1),
                "luz": round(self.luz, 0),
                # CO2 y radiación: None (null) si la zona no tiene ese sensor; nunca se rellena con 0.
                "co2": None if self.co2 is None else round(self.co2, 0),
                "radiacion": None if self.radiacion is None else round(self.radiacion, 0),
            },
            "actuadores": {
                "bomba": "encendido" if self.bomba else "apagado",
                "ventilador": "encendido" if self.ventilador else "apagado",
                "luces": "encendido" if self.luces else "apagado",
            },
            "modo": self.modo,
        }


# Depósito simulado: solo conductividad y disponibilidad de agua (no hay sensor de nivel en porcentaje).
class DepositoSimulado:
    # Valor medio de la conductividad simulada, en mS/cm.
    EC_OBJETIVO = 1.8

    # Crea el depósito con una semilla opcional.
    def __init__(self, semilla: int | None = None) -> None:
        # Generador aleatorio propio.
        self._azar = random.Random(semilla)
        # Conductividad inicial.
        self.conductividad_ec = self.EC_OBJETIVO

    # Avanza la simulación un paso.
    def paso(self) -> None:
        # La conductividad vuelve lentamente a su media con un poco de ruido.
        self.conductividad_ec += (self.EC_OBJETIVO - self.conductividad_ec) * 0.05 + self._azar.gauss(0, 0.01)
        # Mantiene el valor en un rango físico razonable.
        self.conductividad_ec = _limitar(self.conductividad_ec, 0.1, 5.0)

    # Devuelve una foto del estado en el formato del contrato MQTT.
    def instantanea(self) -> dict:
        # nivel_agua es None porque se simula un interruptor de nivel, que solo indica si hay agua.
        return {
            "mediciones": {
                "conductividad_ec": round(self.conductividad_ec, 2),
                "nivel_agua": None,
                "agua_disponible": True,
            }
        }
