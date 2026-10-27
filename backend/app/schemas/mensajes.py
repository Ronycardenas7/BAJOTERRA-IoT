# Validación de los mensajes MQTT entrantes. Es la "puerta de entrada": nada llega a los servicios sin pasar por aquí.
# Regla: un mensaje inválido se rechaza con MensajeInvalido; el dato ausente se guarda como None, nunca como 0.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# json interpreta el texto JSON de los mensajes.
import json
# math.isfinite descarta NaN e infinito, que JSON de Python acepta por error.
import math
# re valida el formato del identificador de dispositivo.
import re
# uuid valida que los identificadores sean UUID bien formados.
import uuid

# Constantes del dominio: valores permitidos y rangos físicos.
from app.domain.constantes import (
    ACTUADORES,
    CALIDADES,
    ESTADOS_ACTUADOR,
    ESTADOS_DISPOSITIVO,
    MEDICIONES_DEPOSITO,
    MEDICIONES_ZONA,
    MODOS,
    ORIGENES,
    RANGOS,
    RESULTADOS_CONFIRMACION,
)
# Error que se lanza cuando un mensaje no cumple el contrato.
from app.domain.errores import MensajeInvalido
# Conversión de texto ISO a fecha.
from app.domain.tiempo import desde_iso

# Tamaño máximo aceptado para un mensaje, en bytes (protege la memoria ante mensajes enormes).
MAX_BYTES = 4096
# Formato permitido para identificadores de dispositivo: minúsculas, números y guiones.
PATRON_DISPOSITIVO = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")


# Convierte los bytes recibidos en un diccionario JSON.
def cargar_json(crudo: bytes) -> dict:
    # Rechaza mensajes demasiado grandes antes de intentar leerlos.
    if len(crudo) > MAX_BYTES:
        # Informa el límite para que sea fácil de corregir.
        raise MensajeInvalido(f"el mensaje supera {MAX_BYTES} bytes")
    # Intenta decodificar el texto y leer el JSON.
    try:
        # Decodifica UTF-8 y convierte el texto a objetos de Python.
        datos = json.loads(crudo.decode("utf-8"))
    # Captura texto con bytes inválidos o JSON mal formado.
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        # Relanza como error del dominio con la causa original.
        raise MensajeInvalido(f"JSON inválido: {error}") from None
    # El contrato exige un objeto JSON (no una lista ni un número suelto).
    if not isinstance(datos, dict):
        # Mensaje claro sobre lo esperado.
        raise MensajeInvalido("el mensaje debe ser un objeto JSON")
    # Devuelve el diccionario ya leído.
    return datos


# Valida el identificador de un dispositivo que viene en el tema MQTT.
def validar_id_dispositivo(valor: str) -> str:
    # Comprueba el formato con la expresión regular.
    if not PATRON_DISPOSITIVO.match(valor):
        # Si no cumple, se rechaza.
        raise MensajeInvalido(f"identificador de dispositivo inválido: {valor!r}")
    # Devuelve el mismo valor, ya validado.
    return valor


# Lee un campo de texto obligatorio, opcionalmente restringido a una lista de valores.
def _texto(datos: dict, campo: str, permitidos: tuple | None = None) -> str:
    # Obtiene el valor del campo (None si no existe).
    valor = datos.get(campo)
    # Debe ser un texto no vacío.
    if not isinstance(valor, str) or not valor:
        # Indica cuál campo falló.
        raise MensajeInvalido(f"el campo '{campo}' es obligatorio y debe ser texto")
    # Si hay lista de valores permitidos, el texto debe estar en ella.
    if permitidos is not None and valor not in permitidos:
        # Muestra los valores permitidos para facilitar la corrección.
        raise MensajeInvalido(f"el campo '{campo}' debe ser uno de {list(permitidos)}, pero es {valor!r}")
    # Devuelve el texto válido.
    return valor


# Lee un identificador UUID obligatorio.
def _uuid(datos: dict, campo: str) -> str:
    # Obtiene el texto del campo.
    texto = _texto(datos, campo)
    # Intenta interpretarlo como UUID.
    try:
        # uuid.UUID lanza ValueError si el formato es incorrecto.
        uuid.UUID(texto)
    # Captura el formato incorrecto.
    except ValueError:
        # Relanza como error del dominio.
        raise MensajeInvalido(f"el campo '{campo}' debe ser un UUID válido") from None
    # Devuelve el UUID original en texto.
    return texto


# Lee una fecha obligatoria en formato ISO 8601 con zona horaria.
def _fecha(datos: dict, campo: str):
    # Obtiene el texto del campo.
    texto = _texto(datos, campo)
    # Intenta convertirlo a datetime en UTC.
    try:
        # desde_iso exige zona horaria y lanza ValueError si el formato es incorrecto.
        return desde_iso(texto)
    # Captura formato inválido o fecha sin zona horaria.
    except ValueError as error:
        # Relanza como error del dominio con la causa.
        raise MensajeInvalido(f"el campo '{campo}' no es una fecha válida: {error}") from None


# Valida un número opcional dentro de un rango. None significa "dato ausente".
def _numero_o_nulo(valor, nombre: str) -> float | None:
    # El dato ausente se acepta y se conserva como None.
    if valor is None:
        # No se inventa un cero.
        return None
    # En Python bool es un tipo de int; se descarta explícitamente (true no es un número de medición).
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        # Mensaje claro sobre el tipo esperado.
        raise MensajeInvalido(f"la medición '{nombre}' debe ser un número o null")
    # NaN e infinito no son mediciones válidas.
    if not math.isfinite(valor):
        # Se rechaza.
        raise MensajeInvalido(f"la medición '{nombre}' no es un número finito")
    # Busca el rango físico permitido para esta medición.
    minimo, maximo = RANGOS[nombre]
    # Comprueba que el valor esté dentro del rango.
    if not minimo <= valor <= maximo:
        # Informa el rango para facilitar el diagnóstico.
        raise MensajeInvalido(f"la medición '{nombre}'={valor} está fuera del rango [{minimo}, {maximo}]")
    # Devuelve el número como decimal.
    return float(valor)


# Valida el objeto "mediciones": solo claves permitidas; las que faltan quedan como None.
def _mediciones(datos: dict, permitidas: tuple, booleanas: tuple = ()) -> dict:
    # Obtiene el objeto; si falta se considera vacío.
    bruto = datos.get("mediciones", {})
    # Debe ser un objeto JSON.
    if not isinstance(bruto, dict):
        # Mensaje claro.
        raise MensajeInvalido("el campo 'mediciones' debe ser un objeto")
    # Detecta claves que el contrato no conoce (por ejemplo, errores de escritura).
    desconocidas = sorted(set(bruto) - set(permitidas))
    # Si hay claves desconocidas, se rechaza todo el mensaje.
    if desconocidas:
        # Lista las claves para que se vean fácil.
        raise MensajeInvalido(f"mediciones desconocidas: {desconocidas}")
    # Diccionario de resultado.
    resultado = {}
    # Recorre cada medición permitida, exista o no en el mensaje.
    for nombre in permitidas:
        # Obtiene el valor (None si no vino).
        valor = bruto.get(nombre)
        # Las mediciones booleanas (como agua_disponible) aceptan true, false o null.
        if nombre in booleanas:
            # Si no es booleano ni null, se rechaza.
            if valor is not None and not isinstance(valor, bool):
                # Mensaje claro.
                raise MensajeInvalido(f"la medición '{nombre}' debe ser true, false o null")
            # Guarda el valor tal cual.
            resultado[nombre] = valor
        # Las demás son números dentro de un rango.
        else:
            # Valida el número (o None).
            resultado[nombre] = _numero_o_nulo(valor, nombre)
    # Devuelve todas las mediciones normalizadas.
    return resultado


# Valida el objeto "actuadores": estado REPORTADO de bomba, ventilador y luces.
def _actuadores(datos: dict) -> dict:
    # Obtiene el objeto; si falta se considera vacío.
    bruto = datos.get("actuadores", {})
    # Debe ser un objeto JSON.
    if not isinstance(bruto, dict):
        # Mensaje claro.
        raise MensajeInvalido("el campo 'actuadores' debe ser un objeto")
    # Detecta actuadores que el contrato no conoce.
    desconocidos = sorted(set(bruto) - set(ACTUADORES))
    # Si hay alguno, se rechaza el mensaje.
    if desconocidos:
        # Lista los nombres.
        raise MensajeInvalido(f"actuadores desconocidos: {desconocidos}")
    # Diccionario de resultado.
    resultado = {}
    # Recorre cada actuador conocido.
    for nombre in ACTUADORES:
        # Obtiene el estado reportado (None si no vino).
        valor = bruto.get(nombre)
        # Debe ser un estado permitido o null.
        if valor is not None and valor not in ESTADOS_ACTUADOR:
            # Mensaje claro con los valores permitidos.
            raise MensajeInvalido(f"el actuador '{nombre}' debe ser uno de {list(ESTADOS_ACTUADOR)} o null")
        # Guarda el estado (o None).
        resultado[nombre] = valor
    # Devuelve los estados normalizados.
    return resultado


# Valida la telemetría de una zona y devuelve un diccionario con los campos ya normalizados.
def validar_telemetria_zona(datos: dict) -> dict:
    # Cada campo se valida por separado; el primero que falle detiene el proceso con MensajeInvalido.
    modo = datos.get("modo")
    # El modo es opcional, pero si viene debe ser conocido.
    if modo is not None and modo not in MODOS:
        # Mensaje claro con los valores permitidos.
        raise MensajeInvalido(f"el campo 'modo' debe ser uno de {list(MODOS)} o null")
    # Arma el resultado con todos los campos del contrato.
    return {
        "id_mensaje": _uuid(datos, "id_mensaje"),
        "dispositivo": validar_id_dispositivo(_texto(datos, "dispositivo")),
        "origen": _texto(datos, "origen", ORIGENES),
        "medido_en": _fecha(datos, "medido_en"),
        "calidad": _texto(datos, "calidad", CALIDADES),
        "mediciones": _mediciones(datos, MEDICIONES_ZONA),
        "actuadores": _actuadores(datos),
        "modo": modo,
    }


# Valida la telemetría de un depósito de agua.
def validar_telemetria_deposito(datos: dict) -> dict:
    # Arma el resultado con los campos del contrato (agua_disponible es booleana).
    return {
        "id_mensaje": _uuid(datos, "id_mensaje"),
        "dispositivo": validar_id_dispositivo(_texto(datos, "dispositivo")),
        "origen": _texto(datos, "origen", ORIGENES),
        "medido_en": _fecha(datos, "medido_en"),
        "calidad": _texto(datos, "calidad", CALIDADES),
        "mediciones": _mediciones(datos, MEDICIONES_DEPOSITO, booleanas=("agua_disponible",)),
    }


# Valida el mensaje de estado de conexión de un dispositivo.
def validar_estado_dispositivo(datos: dict) -> dict:
    # Solo hacen falta el estado y el origen; la hora la pone el backend al recibirlo.
    return {
        "estado": _texto(datos, "estado", ESTADOS_DISPOSITIVO),
        "origen": _texto(datos, "origen", ORIGENES),
    }


# Valida la confirmación que un dispositivo envía después de recibir un comando.
def validar_confirmacion(datos: dict) -> dict:
    # El detalle es opcional; si viene debe ser texto corto.
    detalle = datos.get("detalle")
    # Comprueba tipo y largo del detalle.
    if detalle is not None and (not isinstance(detalle, str) or len(detalle) > 200):
        # Mensaje claro.
        raise MensajeInvalido("el campo 'detalle' debe ser texto de hasta 200 caracteres")
    # Arma el resultado con los campos del contrato.
    return {
        "id_comando": _uuid(datos, "id_comando"),
        "dispositivo": validar_id_dispositivo(_texto(datos, "dispositivo")),
        "origen": _texto(datos, "origen", ORIGENES),
        "resultado": _texto(datos, "resultado", RESULTADOS_CONFIRMACION),
        "confirmado_en": _fecha(datos, "confirmado_en"),
        "detalle": detalle,
    }
