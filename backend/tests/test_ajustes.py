# Pruebas de la lectura de configuración desde variables de entorno.

# pytest ejecuta las pruebas.
import pytest

# Clase a probar.
from app.config.ajustes import Ajustes


# Sin variables se usan los valores por defecto.
def test_valores_por_defecto():
    # Entorno vacío.
    ajustes = Ajustes.desde_entorno({})
    # Broker local y prefijo del proyecto.
    assert (ajustes.mqtt_host, ajustes.mqtt_puerto, ajustes.mqtt_prefijo) == ("localhost", 1883, "bajoterra/01")


# Las variables se leen y el prefijo se limpia de barras sobrantes.
def test_lee_variables():
    # Entorno con valores propios.
    ajustes = Ajustes.desde_entorno({"MQTT_HOST": "mosquitto", "MQTT_PUERTO": "1884", "MQTT_PREFIJO": "/bajoterra/01/"})
    # Se aplican los valores.
    assert (ajustes.mqtt_host, ajustes.mqtt_puerto, ajustes.mqtt_prefijo) == ("mosquitto", 1884, "bajoterra/01")


# Un puerto que no es número falla al arrancar, con un mensaje que nombra la variable.
def test_puerto_invalido():
    # Texto no numérico.
    with pytest.raises(ValueError, match="MQTT_PUERTO"):
        Ajustes.desde_entorno({"MQTT_PUERTO": "abc"})
    # Número fuera de rango.
    with pytest.raises(ValueError, match="MQTT_PUERTO"):
        Ajustes.desde_entorno({"MQTT_PUERTO": "70000"})


# Un nivel de log desconocido falla al arrancar.
def test_nivel_log_invalido():
    # "RUIDOSO" no es un nivel conocido.
    with pytest.raises(ValueError, match="NIVEL_LOG"):
        Ajustes.desde_entorno({"NIVEL_LOG": "ruidoso"})
