# Errores propios del dominio. La capa API los traduce a respuestas HTTP y la capa MQTT los registra y descarta.

# Clase base: todos los errores esperados del sistema heredan de ella.
class ErrorDominio(Exception):
    # Código corto y estable que la web puede usar para reconocer el error.
    codigo = "error_dominio"
    # Código HTTP que se devolverá cuando el error llegue a la API.
    estado_http = 400

    # Constructor: guarda el mensaje legible para personas.
    def __init__(self, mensaje: str) -> None:
        # Inicializa la excepción base con el mismo mensaje (así aparece en los logs).
        super().__init__(mensaje)
        # Guarda el mensaje para poder enviarlo en la respuesta JSON.
        self.mensaje = mensaje


# La petición HTTP trae datos que no cumplen las reglas (campo faltante, valor no permitido...).
class DatosInvalidos(ErrorDominio):
    # Código estable del error.
    codigo = "datos_invalidos"
    # 400 = petición incorrecta.
    estado_http = 400


# Se pidió una zona que no existe.
class ZonaDesconocida(ErrorDominio):
    # Código estable del error.
    codigo = "zona_desconocida"
    # 404 = recurso no encontrado.
    estado_http = 404


# Se pidió un comando que no está registrado.
class ComandoNoEncontrado(ErrorDominio):
    # Código estable del error.
    codigo = "comando_no_encontrado"
    # 404 = recurso no encontrado.
    estado_http = 404


# No hay conexión con el broker MQTT, así que no se puede enviar la orden.
class BrokerNoDisponible(ErrorDominio):
    # Código estable del error.
    codigo = "broker_no_disponible"
    # 503 = servicio no disponible por el momento.
    estado_http = 503


# Un mensaje MQTT recibido no cumple el contrato (JSON roto, campo fuera de rango...).
class MensajeInvalido(ErrorDominio):
    # Código estable del error.
    codigo = "mensaje_invalido"
    # 422 = no se puede procesar el contenido (casi nunca llega a HTTP; se usa para registrar).
    estado_http = 422
