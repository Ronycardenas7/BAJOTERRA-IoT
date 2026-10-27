# Pruebas del modelo físico del simulador (sin MQTT).

# datetime/timedelta/timezone para armar comandos con caducidad.
from datetime import datetime, timedelta, timezone

# Clases a probar.
from sim.modelos import PERFILES, DepositoSimulado, ZonaSimulada
# Conversión de fechas a texto.
from sim.tiempo import a_iso

# Instante fijo usado como "ahora" en los comandos de prueba.
AHORA = datetime(2026, 10, 26, 16, 0, 0, tzinfo=timezone.utc)


# Crea una zona (por defecto la árida) reproducible (con semilla) y con límites de prueba.
def nueva_zona(nombre="arida", bomba_max_s=60.0, manual_s=120.0):
    # Semilla fija para que las pruebas no dependan del azar.
    return ZonaSimulada(PERFILES[nombre], bomba_max_s, manual_s, semilla=1, ahora=0.0)


# Arma un comando válido; "cambios" permite modificarlo.
def comando(**cambios):
    # Comando base: encender la bomba de la zona árida, vence en 30 s.
    base = {
        "id_comando": "5f0d6a7e-6d0e-4b5e-9d57-3f1d6d1a7b11",
        "zona": "arida",
        "actuador": "bomba",
        "estado_solicitado": "encendido",
        "caduca_en": a_iso(AHORA + timedelta(seconds=30)),
    }
    # Aplica los cambios.
    base.update(cambios)
    # Devuelve el comando.
    return base


# Durante una hora simulada, las mediciones se mantienen dentro de rangos físicos válidos.
def test_mediciones_siempre_dentro_de_rango():
    # Una zona de cada tipo.
    for nombre in tuple(PERFILES):
        # Zona reproducible.
        zona = nueva_zona(nombre)
        # 720 pasos de 5 s = 1 hora.
        for paso in range(1, 721):
            # Avanza 5 s.
            zona.paso(paso * 5.0)
            # Toma la foto del estado.
            m = zona.instantanea()["mediciones"]
            # Cada medición dentro de su rango físico.
            assert -40 <= m["temperatura"] <= 85
            assert 0 <= m["humedad_ambiente"] <= 100
            assert 0 <= m["humedad_sustrato"] <= 100
            assert 0 <= m["luz"] <= 200000
            # CO2 y radiación: o son null (sin sensor) o están dentro de rango.
            assert m["co2"] is None or 250 <= m["co2"] <= 5000
            assert m["radiacion"] is None or 0 <= m["radiacion"] <= 1500


# Con la bomba encendida el sustrato se humedece; con la bomba apagada se seca.
def test_bomba_humedece_el_sustrato():
    # Zona en modo manual para que el control automático no interfiera.
    zona = nueva_zona()
    # Orden manual de encender la bomba.
    assert zona.aplicar_comando(comando(), AHORA, 0.0)[0] == "ejecutado"
    # Humedad antes de regar.
    antes = zona.humedad_sustrato
    # Avanza 10 s con la bomba encendida.
    zona.paso(10.0)
    # El sustrato subió.
    assert zona.humedad_sustrato > antes


# La bomba no puede funcionar continuamente más que el límite local, aunque alguien la pida encendida.
def test_limite_de_seguridad_de_la_bomba():
    # Límite de 20 s.
    zona = nueva_zona(bomba_max_s=20.0, manual_s=600.0)
    # Enciende la bomba manualmente en t=0.
    zona.aplicar_comando(comando(), AHORA, 0.0)
    # A los 10 s sigue encendida.
    zona.paso(10.0)
    assert zona.bomba is True
    # A los 25 s el límite la apagó.
    zona.paso(25.0)
    assert zona.bomba is False


# El control automático enciende la bomba cuando el sustrato está seco y la apaga al humedecerse.
def test_control_automatico_de_riego():
    # Zona automática.
    zona = nueva_zona()
    # Fuerza un sustrato seco (por debajo del umbral bajo de la zona árida).
    zona.humedad_sustrato = 5.0
    # Un paso: debe encender la bomba.
    zona.paso(5.0)
    assert zona.bomba is True
    # Fuerza un sustrato húmedo (por encima del umbral alto).
    zona.humedad_sustrato = 80.0
    # Otro paso: debe apagar la bomba.
    zona.paso(10.0)
    assert zona.bomba is False


# Un comando repetido no se ejecuta dos veces.
def test_comando_duplicado():
    # Zona nueva.
    zona = nueva_zona()
    # La primera vez se ejecuta.
    assert zona.aplicar_comando(comando(), AHORA, 0.0)[0] == "ejecutado"
    # La segunda vez (mismo id) se informa duplicado.
    assert zona.aplicar_comando(comando(), AHORA, 1.0)[0] == "duplicado"


# Un comando vencido no se ejecuta (importante tras una reconexión).
def test_comando_caducado():
    # Zona nueva.
    zona = nueva_zona()
    # El comando venció hace 10 s.
    vencido = comando(caduca_en=a_iso(AHORA - timedelta(seconds=10)))
    # Se informa caducado y la bomba sigue apagada.
    assert zona.aplicar_comando(vencido, AHORA, 0.0)[0] == "caducado"
    assert zona.bomba is False


# Comandos mal formados o para otra zona se rechazan sin tocar los actuadores.
def test_comandos_rechazados():
    # Zona nueva.
    zona = nueva_zona()
    # Casos inválidos (cada uno con un id distinto para no chocar con la detección de duplicados).
    casos = [
        comando(id_comando="id-1", zona="humeda"),
        comando(id_comando="id-2", actuador="calefactor"),
        comando(id_comando="id-3", estado_solicitado="medio"),
        comando(id_comando="id-4", caduca_en="mañana"),
        comando(id_comando="id-5", caduca_en=None),
    ]
    # Cada uno debe rechazarse.
    for caso in casos:
        # Resultado esperado: rechazado.
        assert zona.aplicar_comando(caso, AHORA, 0.0)[0] == "rechazado", caso
    # Sin id no se puede ni confirmar.
    assert zona.aplicar_comando({"actuador": "bomba"}, AHORA, 0.0)[0] == "rechazado"
    # Ningún actuador cambió.
    assert zona.bomba is False and zona.ventilador is False


# Una orden manual pone la zona en modo manual y, pasado el tiempo, vuelve al automático.
def test_modo_manual_vuelve_a_automatico():
    # Modo manual de 30 s.
    zona = nueva_zona(manual_s=30.0)
    # Orden manual en t=0.
    zona.aplicar_comando(comando(actuador="ventilador"), AHORA, 0.0)
    # Queda en modo manual.
    assert zona.modo == "manual"
    # A los 10 s sigue manual.
    zona.paso(10.0)
    assert zona.modo == "manual"
    # A los 40 s volvió al automático.
    zona.paso(40.0)
    assert zona.modo == "automatico"


# El depósito reporta que hay agua y deja el nivel en porcentaje como nulo (no hay sensor de nivel).
def test_deposito():
    # Depósito reproducible.
    deposito = DepositoSimulado(semilla=1)
    # Avanza un paso.
    deposito.paso()
    # Foto del estado.
    mediciones = deposito.instantanea()["mediciones"]
    # Hay agua disponible.
    assert mediciones["agua_disponible"] is True
    # El nivel en porcentaje es nulo, no cero.
    assert mediciones["nivel_agua"] is None
    # La conductividad está en un rango razonable.
    assert 0.1 <= mediciones["conductividad_ec"] <= 5.0


# Cada zona solo informa los sensores que tiene: CO2 solo en la selvática, radiación solo en la árida (el resto, null).
def test_sensores_por_zona():
    # Foto inicial de cada zona.
    fotos = {n: nueva_zona(n).instantanea()["mediciones"] for n in PERFILES}
    # La zona árida mide radiación pero no CO2.
    assert fotos["arida"]["radiacion"] is not None and fotos["arida"]["co2"] is None
    # La húmeda no tiene ninguno de los dos.
    assert fotos["humeda"]["radiacion"] is None and fotos["humeda"]["co2"] is None
    # La selvática mide CO2 pero no radiación.
    assert fotos["selvatica"]["co2"] is not None and fotos["selvatica"]["radiacion"] is None


# Una orden manual enciende las luces LED y la luz medida sube respecto a la natural.
def test_orden_enciende_luces():
    # Zona selvática reproducible.
    zona = nueva_zona("selvatica")
    # Orden de encender las luces.
    resultado, _ = zona.aplicar_comando(
        comando(id_comando="luz-1", zona="selvatica", actuador="luces"), AHORA, 0.0
    )
    # Fue ejecutada y el estado reportado es "encendido".
    assert resultado == "ejecutado"
    assert zona.instantanea()["actuadores"]["luces"] == "encendido"
    # Tras un paso, la luz medida incluye el aporte del LED.
    zona.paso(5.0)
    assert zona.luz > zona._luz_natural


# Con el CO2 sobre el máximo, el control automático enciende el extractor en la zona selvática.
def test_co2_alto_enciende_extractor():
    # Zona selvática reproducible, en modo automático.
    zona = nueva_zona("selvatica")
    # Fuerza un CO2 muy alto.
    zona.co2 = 1500.0
    # Un paso de simulación activa el control automático.
    zona.paso(5.0)
    # El extractor quedó encendido.
    assert zona.ventilador is True


# En la zona selvática, con luz natural bajo el mínimo, el control automático enciende los LED.
def test_luz_baja_enciende_leds():
    # Zona selvática reproducible.
    zona = nueva_zona("selvatica")
    # Luz natural muy baja (el paso la recalcula, así que se baja el mínimo hacia arriba en el perfil real).
    # Se avanza hasta el valle de la oscilación (fase -1 en 3/4 del ciclo = 450 s).
    zona.paso(450.0)
    # Con luz natural de 3600 lux (< 3800) deben estar encendidos.
    assert zona.luces is True
