# Pruebas de integración liviana: mensajes MQTT simulados -> servicios -> API HTTP. Sin broker real.

# datetime para fechas de confirmación.
from datetime import datetime, timezone

# pytest ejecuta las pruebas.
import pytest

# Fábrica de la aplicación y ajustes.
from app import create_app
from app.config.ajustes import Ajustes
# Generadores de mensajes de prueba y cliente falso.
from tests.conftest import ClienteMqttFalso, a_bytes, carga_deposito, carga_zona

# Prefijo de temas usado por defecto.
P = "bajoterra/01"


# Fixture: cliente MQTT falso compartido por la aplicación y la prueba.
@pytest.fixture
def cliente():
    # Cliente conectado y sin mensajes.
    return ClienteMqttFalso()


# Fixture: cliente HTTP de pruebas de Flask conectado a la aplicación con el cliente falso.
@pytest.fixture
def http(cliente):
    # Crea la aplicación con ajustes por defecto y el cliente falso (así no se conecta a ningún broker).
    app = create_app(Ajustes(), cliente_mqtt=cliente)
    # test_client permite hacer peticiones sin levantar un servidor.
    return app.test_client()


# /salud informa el estado de la conexión MQTT.
def test_salud(http, cliente):
    # Con broker conectado.
    assert http.get("/salud").get_json() == {"estado": "ok", "mqtt_conectado": True}
    # Se corta la conexión.
    cliente.conectado = False
    # Ahora el estado es degradado, pero el backend sigue respondiendo.
    assert http.get("/salud").get_json()["estado"] == "degradado"


# Un mensaje de telemetría recibido por MQTT aparece en /api/resumen.
def test_telemetria_llega_al_resumen(http, cliente):
    # Busca el manejador que recibe la telemetría de zonas.
    manejador = cliente.manejador(f"{P}/zonas/+/telemetria")
    # Simula la llegada de un mensaje en el tema de la zona árida.
    manejador(f"{P}/zonas/arida/telemetria", a_bytes(carga_zona()))
    # Consulta el resumen por HTTP.
    resumen = http.get("/api/resumen").get_json()
    # La lectura está en la zona correcta.
    assert resumen["zonas"]["arida"]["lectura"]["mediciones"]["temperatura"] == 19.5
    # Y la otra zona sigue sin datos.
    assert resumen["zonas"]["humeda"]["lectura"] is None


# Mensajes malos se descartan sin lanzar excepciones (no deben tumbar el hilo MQTT).
def test_mensajes_malos_se_descartan(http, cliente):
    # Manejador de telemetría de zonas.
    manejador = cliente.manejador(f"{P}/zonas/+/telemetria")
    # JSON roto: no debe lanzar excepción.
    manejador(f"{P}/zonas/arida/telemetria", b"{no es json")
    # Zona que no existe: se descarta.
    manejador(f"{P}/zonas/tomate/telemetria", a_bytes(carga_zona()))
    # Valor fuera de rango: se descarta.
    manejador(f"{P}/zonas/arida/telemetria", a_bytes(carga_zona(mediciones={"temperatura": 999})))
    # Tras todo eso no hay ninguna lectura guardada.
    assert http.get("/api/resumen").get_json()["zonas"]["arida"]["lectura"] is None


# Telemetría de depósito y estado de dispositivo.
def test_deposito_y_estado(http, cliente):
    # Llega telemetría del depósito principal.
    cliente.manejador(f"{P}/depositos/+/telemetria")(f"{P}/depositos/principal/telemetria", a_bytes(carga_deposito()))
    # Llega el estado "en línea" del dispositivo del depósito.
    cliente.manejador(f"{P}/dispositivos/+/estado")(
        f"{P}/dispositivos/sim-deposito/estado", a_bytes({"estado": "en_linea", "origen": "simulado"})
    )
    # Consulta el resumen.
    deposito = http.get("/api/resumen").get_json()["depositos"]["principal"]
    # La conductividad llegó.
    assert deposito["lectura"]["mediciones"]["conductividad_ec"] == 1.8
    # La conexión refleja el estado informado.
    assert deposito["conexion"]["estado"] == "en_linea"


# Ciclo completo de un comando: HTTP -> publicación MQTT -> confirmación MQTT -> consulta HTTP.
def test_ciclo_de_comando(http, cliente):
    # La web pide encender la bomba de la zona árida.
    respuesta = http.post("/api/zonas/arida/comandos", json={"actuador": "bomba", "estado": "encendido"})
    # 202 = aceptado y enviado, pero no ejecutado.
    assert respuesta.status_code == 202
    # Datos del comando creado.
    comando = respuesta.get_json()["comando"]
    # Estado inicial: enviado.
    assert comando["estado"] == "enviado"
    # Se publicó exactamente un mensaje.
    assert len(cliente.publicados) == 1
    # Datos del mensaje publicado.
    tema, carga, qos, retain = cliente.publicados[0]
    # En el tema de comandos de la zona árida.
    assert tema == f"{P}/zonas/arida/comandos"
    # Con QoS 1 y SIN retain (no se reenvía a dispositivos que se reconecten).
    assert (qos, retain) == (1, False)
    # Con el id del comando y su caducidad.
    assert carga["id_comando"] == comando["id_comando"] and "caduca_en" in carga
    # El dispositivo confirma por MQTT.
    cliente.manejador(f"{P}/zonas/+/confirmaciones")(
        f"{P}/zonas/arida/confirmaciones",
        a_bytes(
            {
                "id_comando": comando["id_comando"],
                "dispositivo": "sim-zona-arida",
                "origen": "simulado",
                "resultado": "ejecutado",
                "confirmado_en": datetime.now(timezone.utc).isoformat(),
            }
        ),
    )
    # La web consulta el comando.
    final = http.get(f"/api/comandos/{comando['id_comando']}").get_json()["comando"]
    # Ahora figura como ejecutado, con el origen de la confirmación.
    assert final["estado"] == "ejecutado" and final["origen_confirmacion"] == "simulado"
    # Y aparece en la lista de comandos de la zona.
    assert http.get("/api/zonas/arida/comandos").get_json()["comandos"][0]["id_comando"] == comando["id_comando"]


# Errores de la API tienen un formato único y códigos HTTP correctos.
def test_errores_http(http, cliente):
    # Zona inexistente -> 404.
    respuesta = http.post("/api/zonas/tomate/comandos", json={"actuador": "bomba", "estado": "encendido"})
    # Código y formato del error.
    assert respuesta.status_code == 404
    assert respuesta.get_json()["error"]["codigo"] == "zona_desconocida"
    # Actuador inválido -> 400.
    assert http.post("/api/zonas/arida/comandos", json={"actuador": "x", "estado": "encendido"}).status_code == 400
    # Cuerpo que no es JSON -> 400.
    assert http.post("/api/zonas/arida/comandos", data="hola").status_code == 400
    # Límite inválido en el historial -> 400.
    assert http.get("/api/zonas/arida/telemetria?limite=0").status_code == 400
    # Comando inexistente -> 404.
    assert http.get("/api/comandos/nada").status_code == 404
    # Ruta que no existe -> 404 con el mismo formato.
    assert http.get("/api/no-existe").get_json()["error"]["codigo"] == "not_found"
    # Sin broker, pedir un comando -> 503 y NO se publica nada.
    cliente.conectado = False
    # Petición válida pero sin broker.
    sin_broker = http.post("/api/zonas/arida/comandos", json={"actuador": "bomba", "estado": "encendido"})
    # Debe ser 503.
    assert sin_broker.status_code == 503
    # Y no quedó nada publicado.
    assert cliente.publicados == []
