# Constantes del dominio BAJOTERRA: nombres fijos que comparten backend, simulador y web.
# Si un nombre cambia aquí, también debe cambiar en docs/mqtt-topics.md y en el simulador.

# Zonas de evaluación climática del invernadero: tres ecosistemas independientes (sin tildes en los identificadores).
# "arida" = zona árida, "humeda" = zona húmeda, "selvatica" = zona selvática.
ZONAS = ("arida", "humeda", "selvatica")

# Depósitos de agua conocidos. "principal" es PROVISIONAL: falta decidir si habrá uno compartido o uno por zona.
DEPOSITOS = ("principal",)

# Actuadores que se pueden ordenar en cada zona: bomba de agua, ventilador/extractor y luces LED.
ACTUADORES = ("bomba", "ventilador", "luces")

# Estados posibles de un actuador (tanto el solicitado como el reportado por el dispositivo).
ESTADOS_ACTUADOR = ("encendido", "apagado")

# Origen del dato: "real" (hardware) o "simulado" (software). Nunca se debe mezclar ni ocultar.
ORIGENES = ("real", "simulado")

# Calidad que declara el dispositivo para una medición.
CALIDADES = ("buena", "dudosa", "mala")

# Modo de operación de una zona: control automático local o control manual.
MODOS = ("automatico", "manual")

# Resultados que un dispositivo puede informar al confirmar un comando.
RESULTADOS_CONFIRMACION = ("ejecutado", "rechazado", "caducado", "duplicado")

# Estados de conexión de un dispositivo (se publican en el tema "estado").
ESTADOS_DISPOSITIVO = ("en_linea", "desconectado")

# Mediciones permitidas en la telemetría de una zona.
# "co2" (ppm) y "radiacion" (W/m²) solo existen en las zonas que tengan ese sensor; en las demás llegan como null.
MEDICIONES_ZONA = ("temperatura", "humedad_ambiente", "humedad_sustrato", "luz", "co2", "radiacion")

# Mediciones permitidas en la telemetría de un depósito.
MEDICIONES_DEPOSITO = ("conductividad_ec", "nivel_agua", "agua_disponible")

# Rangos físicos aceptados (mínimo, máximo). Un valor fuera de rango se rechaza como inválido.
RANGOS = {
    # Temperatura del aire del compartimento, en grados Celsius.
    "temperatura": (-40.0, 85.0),
    # Humedad relativa del aire, en porcentaje.
    "humedad_ambiente": (0.0, 100.0),
    # Humedad del sustrato, en porcentaje RELATIVO a la calibración del sensor (no es humedad absoluta).
    "humedad_sustrato": (0.0, 100.0),
    # Luz en lux; el máximo cubre la luz solar directa.
    "luz": (0.0, 200000.0),
    # Dióxido de carbono del aire en partes por millón (el aire exterior ronda 420 ppm).
    "co2": (250.0, 5000.0),
    # Radiación solar en vatios por metro cuadrado (el máximo cubre el sol pleno al mediodía).
    "radiacion": (0.0, 1500.0),
    # Conductividad eléctrica de la solución en milisiemens por centímetro.
    "conductividad_ec": (0.0, 20.0),
    # Nivel de agua en porcentaje (solo existe si hay un sensor de nivel adecuado).
    "nivel_agua": (0.0, 100.0),
}

# Unidades de cada medición, para mostrarlas en la web sin repetirlas en el frontend.
UNIDADES = {
    # Temperatura en grados Celsius.
    "temperatura": "°C",
    # Humedad relativa del aire.
    "humedad_ambiente": "% HR",
    # Humedad del sustrato relativa a la calibración.
    "humedad_sustrato": "% rel.",
    # Luz en lux (solo es real si el sensor está calibrado; en simulación es un valor inventado).
    "luz": "lux",
    # Dióxido de carbono en partes por millón.
    "co2": "ppm",
    # Radiación solar en vatios por metro cuadrado.
    "radiacion": "W/m²",
    # Conductividad eléctrica de la solución.
    "conductividad_ec": "mS/cm",
    # Nivel de agua en porcentaje.
    "nivel_agua": "%",
}
