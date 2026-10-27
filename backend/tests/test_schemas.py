# Pruebas de la validación de mensajes MQTT (app/schemas/mensajes.py).

# pytest ejecuta las pruebas y permite comprobar que se lance un error.
import pytest

# Error que debe lanzarse ante mensajes inválidos.
from app.domain.errores import MensajeInvalido
# Funciones a probar.
from app.schemas import mensajes
# Generadores de mensajes de prueba.
from tests.conftest import a_bytes, carga_deposito, carga_zona


# Un mensaje correcto se acepta y las fechas se convierten a datetime en UTC.
def test_telemetria_zona_valida():
    # Valida el mensaje base.
    datos = mensajes.validar_telemetria_zona(carga_zona())
    # La temperatura se conserva como decimal.
    assert datos["mediciones"]["temperatura"] == 19.5
    # La fecha quedó convertida y con zona horaria.
    assert datos["medido_en"].tzinfo is not None


# Un dato ausente (null o faltante) se conserva como None, nunca como cero.
def test_dato_ausente_se_conserva_como_nulo():
    # Humedad de sustrato en null y luz ausente del mensaje.
    datos = mensajes.validar_telemetria_zona(
        carga_zona(mediciones={"temperatura": 20.0, "humedad_sustrato": None})
    )
    # El null se conserva como None.
    assert datos["mediciones"]["humedad_sustrato"] is None
    # La medición que no vino también queda en None.
    assert datos["mediciones"]["luz"] is None


# Un valor fuera del rango físico se rechaza.
def test_rechaza_medicion_fuera_de_rango():
    # Humedad de 150 % es imposible.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(mediciones={"humedad_ambiente": 150}))


# true/false no son números de medición, aunque en Python bool sea un int.
def test_rechaza_booleano_como_medicion():
    # La temperatura "true" debe rechazarse.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(mediciones={"temperatura": True}))


# Una medición con un nombre que el contrato no conoce se rechaza (evita errores de escritura).
def test_rechaza_medicion_desconocida():
    # "temperature" (en inglés) no existe en el contrato.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(mediciones={"temperature": 20}))


# NaN llega como número válido para el lector JSON de Python, pero no es una medición válida.
def test_rechaza_nan():
    # Un JSON con NaN literal.
    crudo = b'{"mediciones": {"temperatura": NaN}}'
    # Primero se lee el JSON (Python lo acepta)...
    datos = mensajes.cargar_json(crudo)
    # ...y luego la validación de rangos lo rechaza.
    with pytest.raises(MensajeInvalido):
        mensajes._mediciones(datos, ("temperatura",))


# Una fecha sin zona horaria es ambigua y se rechaza.
def test_rechaza_fecha_sin_zona_horaria():
    # Fecha sin "Z" ni desplazamiento.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(medido_en="2026-10-26T16:00:00"))


# El id de mensaje debe ser un UUID.
def test_rechaza_id_mensaje_que_no_es_uuid():
    # "abc" no es un UUID.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(id_mensaje="abc"))


# El origen solo puede ser "real" o "simulado".
def test_rechaza_origen_desconocido():
    # "mixto" no es un origen permitido.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(origen="mixto"))


# El depósito acepta agua_disponible booleana y nivel_agua nulo.
def test_telemetria_deposito_valida():
    # Valida el mensaje base de depósito.
    datos = mensajes.validar_telemetria_deposito(carga_deposito())
    # agua_disponible se conserva como booleano.
    assert datos["mediciones"]["agua_disponible"] is True
    # nivel_agua nulo significa "sin sensor de nivel", no cero.
    assert datos["mediciones"]["nivel_agua"] is None


# agua_disponible no puede ser un número.
def test_rechaza_agua_disponible_no_booleana():
    # El valor 1 no es booleano.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_deposito(carga_deposito(mediciones={"agua_disponible": 1}))


# JSON roto y mensajes que no son objetos se rechazan.
def test_cargar_json_rechaza_basura():
    # Texto que no es JSON.
    with pytest.raises(MensajeInvalido):
        mensajes.cargar_json(b"esto no es json")
    # Una lista no es un objeto.
    with pytest.raises(MensajeInvalido):
        mensajes.cargar_json(b"[1, 2, 3]")
    # Bytes que no son UTF-8 válido.
    with pytest.raises(MensajeInvalido):
        mensajes.cargar_json(b"\xff\xfe")


# Un mensaje demasiado grande se rechaza antes de leerlo.
def test_cargar_json_rechaza_mensaje_enorme():
    # Mensaje con más bytes que el máximo.
    with pytest.raises(MensajeInvalido):
        mensajes.cargar_json(b" " * (mensajes.MAX_BYTES + 1))


# La confirmación válida se acepta y una sin resultado conocido se rechaza.
def test_confirmacion():
    # Mensaje de confirmación correcto.
    base = {
        "id_comando": "5f0d6a7e-6d0e-4b5e-9d57-3f1d6d1a7b11",
        "dispositivo": "sim-zona-arida",
        "origen": "simulado",
        "resultado": "ejecutado",
        "confirmado_en": "2026-10-26T16:00:01Z",
    }
    # Se acepta y el detalle ausente queda en None.
    assert mensajes.validar_confirmacion(base)["detalle"] is None
    # Un resultado inventado se rechaza.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_confirmacion({**base, "resultado": "quizas"})


# El identificador de dispositivo solo admite minúsculas, números y guiones.
def test_id_dispositivo():
    # Uno válido pasa.
    assert mensajes.validar_id_dispositivo("sim-zona-arida") == "sim-zona-arida"
    # Uno con mayúsculas, espacios o barras se rechaza.
    for malo in ("Sim Zona", "a/b", "x", "ñandú"):
        # Cada uno debe fallar.
        with pytest.raises(MensajeInvalido):
            mensajes.validar_id_dispositivo(malo)


# a_bytes se usa en otras pruebas; aquí se comprueba que produce JSON legible por cargar_json.
def test_ida_y_vuelta_json():
    # Convierte a bytes y vuelve a leer.
    assert mensajes.cargar_json(a_bytes({"a": 1})) == {"a": 1}


# El CO2 (ppm) y la radiación (W/m²) son mediciones válidas de zona (zona selvática y árida).
def test_co2_y_radiacion_validos():
    # Mensaje con las dos mediciones nuevas.
    datos = mensajes.validar_telemetria_zona(carga_zona(mediciones={"co2": 650.0, "radiacion": 800.0}))
    # Ambas se conservan como decimales.
    assert datos["mediciones"]["co2"] == 650.0
    # La radiación también.
    assert datos["mediciones"]["radiacion"] == 800.0
    # Las que no vinieron quedan como None (nunca como cero).
    assert datos["mediciones"]["temperatura"] is None


# Un CO2 imposible (bajo el aire exterior) o una radiación negativa se rechazan.
@pytest.mark.parametrize("medicion, valor", [("co2", 100.0), ("co2", 9000.0), ("radiacion", -5.0), ("radiacion", 5000.0)])
def test_co2_y_radiacion_fuera_de_rango(medicion, valor):
    # Debe lanzar MensajeInvalido.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(mediciones={medicion: valor}))


# El actuador "luces" (LED) se acepta y se normaliza; uno desconocido se rechaza.
def test_actuador_luces():
    # Estado reportado de las luces.
    datos = mensajes.validar_telemetria_zona(carga_zona(actuadores={"luces": "encendido"}))
    # Se conserva el estado y los demás quedan en None.
    assert datos["actuadores"]["luces"] == "encendido"
    # Un actuador que el contrato no conoce se rechaza.
    with pytest.raises(MensajeInvalido):
        mensajes.validar_telemetria_zona(carga_zona(actuadores={"calefactor": "encendido"}))
