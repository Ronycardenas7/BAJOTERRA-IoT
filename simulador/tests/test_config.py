# Pruebas de la configuración del simulador.

# pytest ejecuta las pruebas.
import pytest

# Clase a probar.
from sim.config import Ajustes


# Sin variables se usan los valores por defecto.
def test_valores_por_defecto():
    # Entorno vacío.
    ajustes = Ajustes.desde_entorno({})
    # Intervalo de 5 s, sin semilla, broker local.
    assert (ajustes.intervalo_s, ajustes.semilla, ajustes.mqtt_host) == (5.0, None, "localhost")


# Las variables se leen y la semilla se convierte a entero.
def test_lee_variables():
    # Entorno con valores propios.
    ajustes = Ajustes.desde_entorno({"SIM_INTERVALO_S": "2", "SIM_SEMILLA": "7", "MQTT_HOST": "mosquitto"})
    # Se aplican los valores.
    assert (ajustes.intervalo_s, ajustes.semilla, ajustes.mqtt_host) == (2.0, 7, "mosquitto")


# Un valor inválido falla al arrancar con un mensaje que nombra la variable.
def test_valor_invalido():
    # Texto no numérico.
    with pytest.raises(ValueError, match="SIM_INTERVALO_S"):
        Ajustes.desde_entorno({"SIM_INTERVALO_S": "rápido"})
    # Intervalo demasiado pequeño.
    with pytest.raises(ValueError, match="SIM_INTERVALO_S"):
        Ajustes.desde_entorno({"SIM_INTERVALO_S": "0"})
