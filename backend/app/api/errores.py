# Traducción de errores a respuestas JSON con un formato único: {"error": {"codigo": ..., "mensaje": ...}}.

# Permite anotaciones de tipos modernas.
from __future__ import annotations

# logging escribe mensajes de diagnóstico.
import logging

# Flask es la aplicación; jsonify crea respuestas JSON.
from flask import Flask, jsonify
# HTTPException es la clase base de errores HTTP de Flask (404, 405...).
from werkzeug.exceptions import HTTPException

# Error base del dominio.
from app.domain.errores import ErrorDominio

# Logger de este módulo.
registro = logging.getLogger(__name__)


# Crea la respuesta de error con el formato común.
def _respuesta(codigo: str, mensaje: str, estado: int):
    # Devuelve (cuerpo JSON, código HTTP).
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), estado


# Registra los manejadores de errores en la aplicación.
def registrar_manejadores_errores(app: Flask) -> None:
    # Errores esperados del dominio: se devuelven con su código HTTP propio.
    @app.errorhandler(ErrorDominio)
    def _dominio(error: ErrorDominio):
        # Usa el código, mensaje y estado definidos en la excepción.
        return _respuesta(error.codigo, error.mensaje, error.estado_http)

    # Errores HTTP estándar (ruta inexistente, método no permitido...).
    @app.errorhandler(HTTPException)
    def _http(error: HTTPException):
        # Usa el nombre y la descripción que ya trae la excepción.
        return _respuesta(error.name.lower().replace(" ", "_"), error.description or error.name, error.code or 500)

    # Cualquier otro error inesperado.
    @app.errorhandler(Exception)
    def _inesperado(error: Exception):
        # Registra el detalle completo en el log (el cliente NO ve detalles internos).
        registro.exception("Error inesperado en la API")
        # Respuesta genérica 500.
        return _respuesta("error_interno", "Ocurrió un error interno; revise los logs del backend", 500)
