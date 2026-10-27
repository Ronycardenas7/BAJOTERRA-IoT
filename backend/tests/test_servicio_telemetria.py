# Pruebas del servicio de telemetría (registro, duplicados, conexión y desactualización).

# pytest ejecuta las pruebas.
import pytest

# Error esperado ante zonas inexistentes.
from app.domain.errores import ZonaDesconocida
# Repositorios en memoria que usa el servicio.
from app.repositories.memoria import RepositorioDispositivosMemoria, RepositorioTelemetriaMemoria
# Esquemas para preparar datos ya validados.
from app.schemas import mensajes
# Servicio a probar.
from app.services.telemetria_service import ServicioTelemetria
# Generadores de mensajes de prueba.
from tests.conftest import carga_deposito, carga_zona


# Fixture: servicio con repositorios en memoria y reloj falso.
@pytest.fixture
def servicio(reloj):
    # Umbral de 15 segundos para considerar un dato desactualizado.
    return ServicioTelemetria(RepositorioTelemetriaMemoria(50), RepositorioDispositivosMemoria(), 15, reloj)


# Una lectura registrada aparece en el resumen con su conexión.
def test_registra_y_aparece_en_resumen(servicio):
    # El dispositivo informa que está en línea.
    servicio.registrar_estado("sim-zona-arida", {"estado": "en_linea", "origen": "simulado"})
    # Llega una lectura válida.
    servicio.registrar_zona("arida", mensajes.validar_telemetria_zona(carga_zona()))
    # Pide el resumen.
    zona = servicio.resumen()["zonas"]["arida"]
    # La lectura está presente.
    assert zona["lectura"]["mediciones"]["temperatura"] == 19.5
    # El origen se conserva para poder etiquetarlo en la web.
    assert zona["lectura"]["origen"] == "simulado"
    # La conexión refleja el estado informado por el dispositivo.
    assert zona["conexion"]["estado"] == "en_linea"
    # Recién llegada: no está desactualizada.
    assert zona["conexion"]["desactualizada"] is False


# Una zona sin lecturas se muestra como desconocida y desactualizada, sin inventar valores.
def test_zona_sin_datos(servicio):
    # Toma la zona húmeda, que no recibió nada.
    zona = servicio.resumen()["zonas"]["humeda"]
    # No hay lectura.
    assert zona["lectura"] is None
    # La conexión es desconocida.
    assert zona["conexion"]["estado"] == "desconocido"
    # Y se considera desactualizada.
    assert zona["conexion"]["desactualizada"] is True


# Pasado el umbral sin lecturas nuevas, el dato se marca desactualizado.
def test_dato_se_vuelve_desactualizado(servicio, reloj):
    # Llega una lectura.
    servicio.registrar_zona("arida", mensajes.validar_telemetria_zona(carga_zona()))
    # Pasan 20 segundos (más que el umbral de 15).
    reloj.avanzar(20)
    # Consulta el resumen.
    conexion = servicio.resumen()["zonas"]["arida"]["conexion"]
    # Debe marcarse desactualizada.
    assert conexion["desactualizada"] is True
    # Y mostrar la antigüedad.
    assert conexion["segundos_desde_ultima_lectura"] == 20.0


# Un mensaje repetido (mismo id) no se guarda dos veces.
def test_ignora_duplicados(servicio):
    # Un mensaje válido.
    datos = mensajes.validar_telemetria_zona(carga_zona())
    # La primera vez se guarda.
    assert servicio.registrar_zona("arida", datos) is True
    # La segunda vez (mismo id) se ignora.
    assert servicio.registrar_zona("arida", datos) is False
    # El historial tiene una sola lectura.
    assert len(servicio.historial_zona("arida", 10)) == 1


# El historial respeta el límite pedido.
def test_historial_respeta_limite(servicio):
    # Guarda 5 lecturas distintas.
    for _ in range(5):
        # Cada carga_zona() trae un id distinto.
        servicio.registrar_zona("arida", mensajes.validar_telemetria_zona(carga_zona()))
    # Pide solo las últimas 3.
    assert len(servicio.historial_zona("arida", 3)) == 3


# Una zona inexistente produce un error claro.
def test_zona_desconocida(servicio):
    # Registrar en una zona que no existe.
    with pytest.raises(ZonaDesconocida):
        servicio.registrar_zona("tomate", mensajes.validar_telemetria_zona(carga_zona()))
    # Pedir el historial de una zona que no existe.
    with pytest.raises(ZonaDesconocida):
        servicio.historial_zona("tomate", 10)


# El depósito guarda agua_disponible sin inventar un nivel en porcentaje.
def test_deposito(servicio):
    # Llega una lectura de depósito.
    servicio.registrar_deposito("principal", mensajes.validar_telemetria_deposito(carga_deposito()))
    # Pide el resumen del depósito.
    deposito = servicio.resumen()["depositos"]["principal"]["lectura"]
    # Hay agua disponible.
    assert deposito["mediciones"]["agua_disponible"] is True
    # El nivel en porcentaje queda nulo porque no hay sensor de nivel.
    assert deposito["mediciones"]["nivel_agua"] is None
