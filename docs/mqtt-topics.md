# Contrato MQTT v1 (borrador implementado)

> **Modo nube (D-010):** el mismo JSON de este documento se envía por HTTPS a la función `registrar_lectura` de Supabase (ver `docs/tiempo-real.md`).
> Diferencias: no hay temas MQTT. El simulador agrega `"zona"` o `"deposito"` para indicar el destino; un ESP32 escribe siempre en la zona asociada a su clave.

Este documento describe los mensajes que se intercambian el **simulador** (y, más adelante, el ESP32), el **broker Mosquitto** y el **backend**.
Es la referencia común: si un nombre cambia aquí, debe cambiar también en `backend/app/domain/constantes.py` y en el simulador.

> Estado: implementado y probado **solo con el simulador**. No se ha probado con hardware real.

## Reglas generales

- Todos los mensajes son **JSON en UTF-8**, de máximo **4096 bytes**.
- Todas las fechas son **ISO 8601 en UTC con zona horaria**, por ejemplo `2026-10-26T16:07:00.123Z`. Una fecha sin zona horaria se rechaza.
- Un **dato ausente se envía como `null`**, nunca como `0`. Una medición que no viene en el mensaje se guarda como ausente.
- Cada mensaje de telemetría lleva `origen`: `"real"` o `"simulado"`. Los datos simulados **nunca** se presentan como reales.
- Cada mensaje de telemetría lleva un `id_mensaje` (UUID). El backend ignora los repetidos (QoS 1 puede entregar duplicados).
- Un mensaje inválido (JSON roto, valor fuera de rango, campo desconocido) **se registra y se descarta**; no detiene el backend.

## Temas

El prefijo es `bajoterra/01` (variable `MQTT_PREFIJO`).

| Tema | Quién publica | Quién escucha | QoS | Retain |
|---|---|---|---|---|
| `bajoterra/01/zonas/{zona}/telemetria` | Dispositivo de la zona | Backend | 0 | No |
| `bajoterra/01/zonas/{zona}/comandos` | Backend | Dispositivo de la zona | 1 | **No** |
| `bajoterra/01/zonas/{zona}/confirmaciones` | Dispositivo de la zona | Backend | 1 | No |
| `bajoterra/01/depositos/{deposito}/telemetria` | Dispositivo del depósito | Backend | 0 | No |
| `bajoterra/01/dispositivos/{id}/estado` | Dispositivo (y su "última voluntad") | Backend | 1 | Sí |

- `{zona}`: `arida`, `humeda` o `selvatica` (sin tildes en el identificador).
- `{deposito}`: `principal` (**provisional**: falta decidir si el depósito es compartido o hay uno por zona).
- `{id}`: identificador del dispositivo, solo minúsculas, números y guiones (2 a 41 caracteres), por ejemplo `sim-zona-selvatica`.

Por qué los comandos **no** usan retain: un mensaje retenido se entregaría de nuevo a un dispositivo que se reconecta, y repetir una orden vieja
(por ejemplo, encender una bomba) puede ser peligroso. Además, cada comando lleva su propia caducidad.

## Telemetría de zona

```json
{
  "id_mensaje": "5f0d6a7e-6d0e-4b5e-9d57-3f1d6d1a7b11",
  "dispositivo": "sim-zona-selvatica",
  "origen": "simulado",
  "medido_en": "2026-10-26T16:07:00.123Z",
  "calidad": "buena",
  "mediciones": {
    "temperatura": 19.5,
    "humedad_ambiente": 70.0,
    "humedad_sustrato": 65.0,
    "luz": 5200.0,
    "co2": 830.0,
    "radiacion": null
  },
  "actuadores": { "bomba": "apagado", "ventilador": "encendido", "luces": "encendido" },
  "modo": "automatico"
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `id_mensaje` | UUID | Obligatorio. |
| `dispositivo` | texto | Obligatorio. |
| `origen` | `real` / `simulado` | Obligatorio. |
| `medido_en` | fecha UTC | Obligatorio. Instante de la medición según el dispositivo. El backend agrega `recibido_en` al recibirlo. |
| `calidad` | `buena` / `dudosa` / `mala` | Obligatorio. |
| `mediciones` | objeto | Solo claves permitidas (abajo); las que faltan se guardan como ausentes. |
| `actuadores` | objeto | Estado **reportado** de `bomba` (bomba de agua), `ventilador` (extractor) y `luces` (LED): `encendido`, `apagado` o `null`. |
| `modo` | `automatico` / `manual` / `null` | Opcional. |

| Medición | Unidad | Rango aceptado | Observación |
|---|---|---|---|
| `temperatura` | °C | -40 a 85 | Aire del compartimento. |
| `humedad_ambiente` | % HR | 0 a 100 | Aire del compartimento. |
| `humedad_sustrato` | % relativo | 0 a 100 | Relativo a la calibración del sensor y del sustrato; no es humedad absoluta. |
| `co2` | ppm | 250 a 5000 | Solo en la zona que tenga sensor (selvática); el resto envía `null`. |
| `radiacion` | W/m² | 0 a 1500 | Solo en la zona que tenga sensor (árida); el resto envía `null`. |
| `luz` | lux | 0 a 200000 | Solo debe usar lux si hay calibración que lo respalde. Una LDR mapeada linealmente **no** demuestra lux reales. |

`true`/`false`, `NaN` e infinito **no** son mediciones válidas.

## Telemetría de depósito

```json
{
  "id_mensaje": "8c1e9f52-3b0a-4f1b-8d7e-0a9d2c5b6e44",
  "dispositivo": "sim-deposito-principal",
  "origen": "simulado",
  "medido_en": "2026-10-26T16:07:00.456Z",
  "calidad": "buena",
  "mediciones": { "conductividad_ec": 1.8, "nivel_agua": null, "agua_disponible": true }
}
```

| Medición | Unidad | Rango | Observación |
|---|---|---|---|
| `conductividad_ec` | mS/cm | 0 a 20 | Mide la solución **en el punto del sensor**; no indica nutrientes individuales. |
| `nivel_agua` | % | 0 a 100 | Solo con un sensor de nivel adecuado. Con un interruptor de nivel va `null`. |
| `agua_disponible` | booleano | `true` / `false` / `null` | Indicador de disponibilidad (por ejemplo, de un interruptor de nivel). |

## Estado de conexión del dispositivo

Cada dispositivo publica `en_linea` (retain) al conectarse y registra una **"última voluntad"** (`desconectado`, retain) para que el broker la
publique si el dispositivo se cae sin despedirse. En una parada ordenada el dispositivo publica `desconectado` él mismo.

```json
{ "estado": "en_linea", "origen": "simulado" }
```

La hora la agrega el backend al recibir el mensaje.

## Comandos

Una orden pasa por etapas que se registran por separado: **solicitado → enviado → confirmado** (o rechazado, caducado, duplicado).
**Una orden enviada no equivale a un actuador encendido**: el estado real es el que el dispositivo reporta en su telemetría.
Tampoco hay caudalímetro: no se afirma flujo real ni litros medidos.

Backend → dispositivo (`.../comandos`):

```json
{
  "id_comando": "0d6b8c1a-8f4a-4f0e-9a52-7a3c1f9e2b10",
  "zona": "selvatica",
  "actuador": "bomba",
  "estado_solicitado": "encendido",
  "solicitado_en": "2026-10-26T16:07:10.000Z",
  "caduca_en": "2026-10-26T16:07:40.000Z"
}
```

Dispositivo → backend (`.../confirmaciones`):

```json
{
  "id_comando": "0d6b8c1a-8f4a-4f0e-9a52-7a3c1f9e2b10",
  "dispositivo": "sim-zona-selvatica",
  "origen": "simulado",
  "resultado": "ejecutado",
  "confirmado_en": "2026-10-26T16:07:10.250Z",
  "detalle": "aplicado en el simulador"
}
```

| `resultado` | Significado |
|---|---|
| `ejecutado` | El dispositivo aplicó la orden. (Una confirmación de transporte **no** demuestra ejecución física: con hardware real, el firmware solo debe confirmar tras actuar.) |
| `rechazado` | La orden era inválida (actuador desconocido, zona equivocada...). |
| `caducado` | La orden llegó después de `caduca_en`; **no** se ejecuta. |
| `duplicado` | El dispositivo ya había procesado ese `id_comando`; **no** se vuelve a ejecutar. |

Reglas de seguridad para el firmware futuro:

- Ignorar y confirmar como `caducado` toda orden con `caduca_en` vencida (importante tras reconectarse).
- Recordar los últimos `id_comando` para no repetir acciones.
- Mantener control local básico y límites de funcionamiento (por ejemplo, tiempo máximo continuo de la bomba) **aunque no haya conexión**.

## Pendiente de decidir

- **ESP-NOW:** el informe lo usa como enlace local. Hay que decidir si habrá nodos ESP-NOW con una puerta de enlace (gateway) que publique en MQTT, o ESP32 conectados directamente al broker. No se implementó ninguna de las dos topologías.
- **Depósito:** compartido o uno por zona.
- **Control de acceso por tema (ACL)** y **TLS** en el broker, antes de abrirlo a la red local para el ESP32 real.
