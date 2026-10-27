# Construcción y lectura de los temas MQTT. Es el único lugar que conoce la forma de los temas.
# El contrato completo está documentado en docs/mqtt-topics.md.

# Permite anotaciones de tipos modernas.
from __future__ import annotations


# Genera los temas a partir de un prefijo común (por ejemplo "bajoterra/01").
class Temas:
    # Guarda el prefijo sin barras sobrantes en los extremos.
    def __init__(self, prefijo: str) -> None:
        # strip("/") evita temas con "//" por un prefijo mal escrito.
        self.prefijo = prefijo.strip("/")

    # Tema donde una zona publica su telemetría.
    def telemetria_zona(self, zona: str) -> str:
        # Ejemplo: bajoterra/01/zonas/arida/telemetria
        return f"{self.prefijo}/zonas/{zona}/telemetria"

    # Tema donde el backend publica los comandos de una zona.
    def comandos_zona(self, zona: str) -> str:
        # Ejemplo: bajoterra/01/zonas/arida/comandos
        return f"{self.prefijo}/zonas/{zona}/comandos"

    # Filtro que recibe la telemetría de TODAS las zonas ("+" reemplaza un nivel completo).
    def filtro_telemetria_zonas(self) -> str:
        # Ejemplo: bajoterra/01/zonas/+/telemetria
        return f"{self.prefijo}/zonas/+/telemetria"

    # Filtro que recibe las confirmaciones de comandos de todas las zonas.
    def filtro_confirmaciones_zonas(self) -> str:
        # Ejemplo: bajoterra/01/zonas/+/confirmaciones
        return f"{self.prefijo}/zonas/+/confirmaciones"

    # Filtro que recibe la telemetría de todos los depósitos.
    def filtro_telemetria_depositos(self) -> str:
        # Ejemplo: bajoterra/01/depositos/+/telemetria
        return f"{self.prefijo}/depositos/+/telemetria"

    # Filtro que recibe el estado de conexión de todos los dispositivos.
    def filtro_estado_dispositivos(self) -> str:
        # Ejemplo: bajoterra/01/dispositivos/+/estado
        return f"{self.prefijo}/dispositivos/+/estado"

    # Separa un tema recibido en (recurso, identificador, tipo). Devuelve None si no cumple el formato.
    def separar(self, tema: str) -> tuple[str, str, str] | None:
        # El tema debe empezar con el prefijo seguido de una barra.
        inicio = self.prefijo + "/"
        # Si no empieza con el prefijo, no es nuestro.
        if not tema.startswith(inicio):
            # Se descarta.
            return None
        # Quita el prefijo y separa el resto por barras.
        partes = tema[len(inicio):].split("/")
        # Debe quedar exactamente: recurso / identificador / tipo.
        if len(partes) != 3:
            # Formato inesperado.
            return None
        # Devuelve la tupla (por ejemplo: "zonas", "arida", "telemetria").
        return partes[0], partes[1], partes[2]
