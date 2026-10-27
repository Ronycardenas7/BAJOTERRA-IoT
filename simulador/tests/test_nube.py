# Pruebas del simulador en modo nube (sin red: se usa un cliente falso que imita a Supabase).

# datetime/timedelta para fabricar horas del servidor.
from datetime import datetime, timedelta, timezone

# Clases a probar.
from sim.nube import SimuladorNube
# Conversión de fechas.
from sim.tiempo import a_iso, ahora_utc


# Cliente falso: guarda las llamadas y responde como lo haría Supabase.
class ClienteFalso:
    # desfase_servidor: cuánto adelanta (o atrasa) la hora del "servidor" respecto del PC.
    def __init__(self, desfase_servidor=timedelta(0), ordenes=None):
        # Lista de llamadas recibidas (nombre de la función y datos).
        self.llamadas = []
        # Desfase simulado.
        self.desfase = desfase_servidor
        # Órdenes pendientes que devolverá una sola vez.
        self.ordenes = ordenes or []

    # Imita ClienteSupabase.rpc.
    def rpc(self, funcion, datos):
        # Registra la llamada.
        self.llamadas.append((funcion, datos))
        # Hora del servidor en formato ISO con zona horaria (como la entrega PostgREST).
        if funcion == "hora_servidor":
            return (datetime.now(timezone.utc) + self.desfase).isoformat()
        # Lecturas: siempre "guardado".
        if funcion == "registrar_lectura":
            return {"estado": "guardado"}
        # Órdenes: las entrega una vez y luego ninguna.
        if funcion == "comandos_pendientes":
            pendientes, self.ordenes = self.ordenes, []
            return pendientes
        # Confirmaciones.
        return {"actualizado": True}


# Crea un simulador reproducible con el cliente falso.
def nuevo(cliente):
    # Semilla fija y límites de prueba.
    return SimuladorNube(cliente, "bjt_prueba", intervalo_s=10, semilla=1, bomba_max_s=60, manual_s=120)


# Con el reloj del PC adelantado 54 min, las lecturas salen con la hora del SERVIDOR (corregida).
def test_corrige_reloj_desfasado():
    # El servidor va 54 minutos "atrás" del PC (es decir, el PC está adelantado).
    cliente = ClienteFalso(desfase_servidor=timedelta(minutes=-54))
    simulador = nuevo(cliente)
    # Mide el desfase.
    simulador.medir_desfase()
    # Envía una ronda de lecturas.
    simulador.enviar_lecturas()
    # Toma las lecturas enviadas.
    lecturas = [d["p_lectura"] for f, d in cliente.llamadas if f == "registrar_lectura"]
    # 3 zonas + 1 depósito.
    assert len(lecturas) == 4
    # La hora de cada lectura está a menos de 5 s de la hora del servidor.
    esperado = datetime.now(timezone.utc) - timedelta(minutes=54)
    for lectura in lecturas:
        assert abs((datetime.fromisoformat(lectura["medido_en"]) - esperado).total_seconds()) < 5
        # Todas se declaran simuladas.
        assert lectura["origen"] == "simulado"


# Las lecturas indican zona o depósito y respetan los sensores de cada zona (null donde no hay sensor).
def test_formato_de_lecturas():
    # Simulador sin desfase.
    cliente = ClienteFalso()
    simulador = nuevo(cliente)
    simulador.enviar_lecturas()
    # Lecturas por zona.
    por_zona = {d["p_lectura"].get("zona", "deposito"): d["p_lectura"] for f, d in cliente.llamadas if f == "registrar_lectura"}
    # Las tres zonas y el depósito.
    assert set(por_zona) == {"arida", "humeda", "selvatica", "deposito"}
    # CO2 solo en la selvática; radiación solo en la árida.
    assert por_zona["selvatica"]["mediciones"]["co2"] is not None and por_zona["arida"]["mediciones"]["co2"] is None
    assert por_zona["arida"]["mediciones"]["radiacion"] is not None and por_zona["humeda"]["mediciones"]["radiacion"] is None
    # Todas usan la clave del simulador.
    assert all(d["p_clave"] == "bjt_prueba" for f, d in cliente.llamadas)


# Una orden pendiente se aplica al modelo y se confirma como "ejecutado" con origen "simulado".
def test_atiende_y_confirma_ordenes():
    # Orden vigente para encender las luces de la zona selvática.
    orden = {"id_comando": "c1", "zona": "selvatica", "actuador": "luces", "estado_solicitado": "encendido",
             "caduca_en": a_iso(ahora_utc() + timedelta(seconds=30))}
    cliente = ClienteFalso(ordenes=[orden])
    simulador = nuevo(cliente)
    # Atiende las órdenes.
    simulador.atender_ordenes()
    # Busca la confirmación enviada.
    confirmaciones = [d for f, d in cliente.llamadas if f == "confirmar_comando"]
    assert len(confirmaciones) == 1
    assert confirmaciones[0]["p_resultado"] == "ejecutado" and confirmaciones[0]["p_origen"] == "simulado"
    # El modelo quedó con las luces encendidas.
    assert simulador._zonas["selvatica"].luces is True


# Una orden vencida no se ejecuta: se confirma como "caducado".
def test_orden_vencida_no_se_ejecuta():
    # Orden que venció hace 10 s.
    orden = {"id_comando": "c2", "zona": "arida", "actuador": "bomba", "estado_solicitado": "encendido",
             "caduca_en": a_iso(ahora_utc() - timedelta(seconds=10))}
    cliente = ClienteFalso(ordenes=[orden])
    simulador = nuevo(cliente)
    simulador.atender_ordenes()
    # Resultado "caducado" y bomba apagada.
    assert [d["p_resultado"] for f, d in cliente.llamadas if f == "confirmar_comando"] == ["caducado"]
    assert simulador._zonas["arida"].bomba is False
