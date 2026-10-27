# Pruebas del servicio de comandos (solicitud, confirmación, caducidad y fallos de envío).

# datetime/timezone para armar fechas de confirmación.
from datetime import timedelta

# pytest ejecuta las pruebas.
import pytest

# Errores esperados.
from app.domain.errores import BrokerNoDisponible, ComandoNoEncontrado, DatosInvalidos, ZonaDesconocida
# Repositorio en memoria.
from app.repositories.memoria import RepositorioComandosMemoria
# Servicio a probar.
from app.services.comandos_service import ServicioComandos


# Fixture: servicio con repositorio en memoria, publicador falso y reloj falso.
@pytest.fixture
def servicio(publicador, reloj):
    # Vida por defecto de 30 segundos.
    return ServicioComandos(RepositorioComandosMemoria(20), publicador, 30, reloj)


# Arma los datos de una confirmación válida para un comando.
def confirmacion(comando, reloj, resultado="ejecutado"):
    # Estructura que entrega la capa de esquemas.
    return {
        "id_comando": comando.id_comando,
        "dispositivo": "sim-zona-arida",
        "origen": "simulado",
        "resultado": resultado,
        "confirmado_en": reloj.ahora + timedelta(seconds=1),
        "detalle": None,
    }


# Solicitar un comando lo registra, lo envía y deja claro que aún no está ejecutado.
def test_solicitar_registra_y_envia(servicio, publicador):
    # Pide encender la bomba de la zona árida.
    comando = servicio.solicitar("arida", "bomba", "encendido")
    # Quedó enviado, no ejecutado.
    assert comando.estado == "enviado"
    # No tiene confirmación todavía.
    assert comando.confirmado_en is None
    # El publicador recibió exactamente ese comando.
    assert publicador.enviados == [comando]
    # La caducidad es solicitado_en + 30 s.
    assert comando.caduca_en - comando.solicitado_en == timedelta(seconds=30)


# Una confirmación "ejecutado" actualiza el comando y conserva quién lo confirmó.
def test_confirmacion_ejecutado(servicio, reloj):
    # Solicita y luego confirma.
    comando = servicio.solicitar("arida", "bomba", "encendido")
    # Registra la confirmación.
    final = servicio.registrar_confirmacion(confirmacion(comando, reloj))
    # El estado final es ejecutado.
    assert final.estado == "ejecutado"
    # Se guarda quién y con qué origen confirmó.
    assert (final.dispositivo, final.origen_confirmacion) == ("sim-zona-arida", "simulado")
    # Y el servicio devuelve lo mismo al consultar.
    assert servicio.obtener(comando.id_comando).estado == "ejecutado"


# La primera confirmación manda: una repetida (por QoS 1) no cambia el resultado.
def test_confirmacion_repetida_se_ignora(servicio, reloj):
    # Solicita y confirma como ejecutado.
    comando = servicio.solicitar("humeda", "ventilador", "encendido")
    # Primera confirmación.
    servicio.registrar_confirmacion(confirmacion(comando, reloj, "ejecutado"))
    # Llega otra distinta (por ejemplo "duplicado" porque el dispositivo vio el id dos veces).
    servicio.registrar_confirmacion(confirmacion(comando, reloj, "duplicado"))
    # El resultado sigue siendo el primero.
    assert servicio.obtener(comando.id_comando).estado == "ejecutado"


# Confirmar un comando desconocido produce un error (la capa MQTT lo registra y lo descarta).
def test_confirmacion_de_comando_desconocido(servicio, reloj, publicador):
    # Crea un comando solo para reutilizar el formato, pero con otro id.
    comando = servicio.solicitar("arida", "bomba", "apagado")
    # Cambia el id por uno que no existe.
    datos = confirmacion(comando, reloj) | {"id_comando": "00000000-0000-4000-8000-000000000000"}
    # Debe fallar con ComandoNoEncontrado.
    with pytest.raises(ComandoNoEncontrado):
        servicio.registrar_confirmacion(datos)


# Si el broker está caído, el comando queda registrado como fallido y se informa el error.
def test_fallo_de_envio(servicio, publicador):
    # Simula broker caído.
    publicador.fallar = True
    # La solicitud lanza BrokerNoDisponible.
    with pytest.raises(BrokerNoDisponible):
        servicio.solicitar("arida", "bomba", "encendido")
    # Se puede ver en la lista que quedó como fallido_envio y sin hora de envío.
    guardado = servicio.listar_zona("arida", 10)[0]
    # Estado de fallo.
    assert guardado.estado == "fallido_envio"
    # No se afirma que salió.
    assert guardado.enviado_en is None


# Valores no permitidos se rechazan antes de enviar nada.
def test_validaciones(servicio, publicador):
    # Zona inexistente.
    with pytest.raises(ZonaDesconocida):
        servicio.solicitar("tomate", "bomba", "encendido")
    # Actuador inexistente.
    with pytest.raises(DatosInvalidos):
        servicio.solicitar("arida", "calefactor", "encendido")
    # Estado inexistente.
    with pytest.raises(DatosInvalidos):
        servicio.solicitar("arida", "bomba", "medio")
    # Vida fuera de rango.
    with pytest.raises(DatosInvalidos):
        servicio.solicitar("arida", "bomba", "encendido", ttl_s=1)
    # Vida booleana (True se parece a 1, pero no es un número válido aquí).
    with pytest.raises(DatosInvalidos):
        servicio.solicitar("arida", "bomba", "encendido", ttl_s=True)
    # Nada de lo anterior llegó al publicador.
    assert publicador.enviados == []


# Consultar un comando inexistente produce un error 404.
def test_obtener_inexistente(servicio):
    # Id que no existe.
    with pytest.raises(ComandoNoEncontrado):
        servicio.obtener("no-existe")


# Se puede pedir encender las luces LED de la zona selvática (nuevo actuador).
def test_comando_luces_en_zona_selvatica(servicio, publicador):
    # Solicita encender las luces de la zona selvática.
    comando = servicio.solicitar("selvatica", "luces", "encendido")
    # Quedó enviado y dirigido a esa zona.
    assert (comando.zona, comando.actuador, comando.estado) == ("selvatica", "luces", "enviado")
