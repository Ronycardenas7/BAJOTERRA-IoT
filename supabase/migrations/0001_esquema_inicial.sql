-- ============================================================================
-- 0001_esquema_inicial.sql — Tablas base del esquema de datos (PostgreSQL / Supabase)
--
-- ESTADO: aplicado el 2026-10-27 en el proyecto Supabase "bajoterra-iot" (región sa-east-1), seguido de 0002.
-- Para otro proyecto: Supabase > SQL Editor > pegar este archivo > Run, y luego 0002.
-- Es idempotente (se puede ejecutar varias veces sin duplicar nada).
--
-- Decisiones de diseño (ver docs/decisiones.md):
--  * Tipos "double precision" (no NUMERIC(4,2)): el esquema histórico no admitía 100,00 % ni miles de lux.
--  * Los datos ausentes se guardan como NULL, nunca como 0.
--  * Cada fila guarda origen (real/simulado), id de mensaje, instante de medición, instante de recepción y calidad.
--  * Las mediciones del depósito van en una tabla aparte de las de las zonas.
--  * Los comandos guardan por separado solicitud, envío y confirmación.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- LECTURAS DE ZONA (arida / humeda / selvatica)
-- ---------------------------------------------------------------------------

-- Crea la tabla solo si todavía no existe.
create table if not exists public.lecturas_zona (
  -- Identificador único del mensaje MQTT (UUID). Como es clave primaria, un mensaje repetido no se guarda dos veces.
  id_mensaje        uuid primary key,
  -- Zona de la lectura; solo se admiten las tres zonas de evaluación.
  zona              text not null check (zona in ('arida', 'humeda', 'selvatica')),
  -- Dispositivo que midió (por ejemplo "sim-zona-arida").
  dispositivo       text not null,
  -- "real" si viene de hardware, "simulado" si viene del simulador. Nunca se mezclan ni se ocultan.
  origen            text not null check (origen in ('real', 'simulado')),
  -- Instante en que el dispositivo midió (UTC).
  medido_en         timestamptz not null,
  -- Instante en que el backend recibió el mensaje (UTC).
  recibido_en       timestamptz not null,
  -- Calidad declarada por el dispositivo.
  calidad           text not null check (calidad in ('buena', 'dudosa', 'mala')),
  -- Temperatura del aire del compartimento, en °C (NULL = dato ausente).
  temperatura       double precision check (temperatura between -40 and 85),
  -- Humedad relativa del aire, en % (NULL = dato ausente).
  humedad_ambiente  double precision check (humedad_ambiente between 0 and 100),
  -- Humedad del sustrato, en % RELATIVO a la calibración del sensor (NULL = dato ausente).
  humedad_sustrato  double precision check (humedad_sustrato between 0 and 100),
  -- Luz en lux; solo es real si el sensor está calibrado (NULL = dato ausente).
  luz               double precision check (luz between 0 and 200000),
  -- CO2 del aire en ppm (NULL = la zona no tiene sensor o el dato está ausente).
  co2               double precision check (co2 between 250 and 5000),
  -- Radiación solar en W/m2 (NULL = la zona no tiene sensor o el dato está ausente).
  radiacion         double precision check (radiacion between 0 and 1500),
  -- Estado REPORTADO de la bomba (no es lo mismo que una orden pendiente).
  bomba             text check (bomba in ('encendido', 'apagado')),
  -- Estado REPORTADO del ventilador/extractor.
  ventilador        text check (ventilador in ('encendido', 'apagado')),
  -- Estado REPORTADO de las luces LED.
  luces             text check (luces in ('encendido', 'apagado')),
  -- Modo de la zona informado por el dispositivo.
  modo              text check (modo in ('automatico', 'manual'))
);

-- Índice para consultar rápido el historial de una zona, de lo más reciente a lo más antiguo.
create index if not exists lecturas_zona_zona_medido_idx
  on public.lecturas_zona (zona, medido_en desc);

-- ---------------------------------------------------------------------------
-- LECTURAS DE DEPÓSITO
-- ---------------------------------------------------------------------------

-- Crea la tabla solo si todavía no existe.
create table if not exists public.lecturas_deposito (
  -- Identificador único del mensaje MQTT (UUID).
  id_mensaje        uuid primary key,
  -- Depósito de la lectura. "principal" es PROVISIONAL: falta decidir si habrá uno compartido o uno por zona.
  deposito          text not null check (deposito in ('principal')),
  -- Dispositivo que midió.
  dispositivo       text not null,
  -- "real" o "simulado".
  origen            text not null check (origen in ('real', 'simulado')),
  -- Instante de la medición (UTC).
  medido_en         timestamptz not null,
  -- Instante de recepción en el backend (UTC).
  recibido_en       timestamptz not null,
  -- Calidad declarada por el dispositivo.
  calidad           text not null check (calidad in ('buena', 'dudosa', 'mala')),
  -- Conductividad eléctrica de la solución, en mS/cm, en el punto del sensor (no mide nutrientes individuales).
  conductividad_ec  double precision check (conductividad_ec between 0 and 20),
  -- Nivel de agua en %. Solo existe si hay un sensor de nivel adecuado; con un interruptor queda NULL.
  nivel_agua        double precision check (nivel_agua between 0 and 100),
  -- Indicador de disponibilidad de agua (por ejemplo, de un interruptor de nivel).
  agua_disponible   boolean
);

-- Índice para consultar el historial de un depósito.
create index if not exists lecturas_deposito_deposito_medido_idx
  on public.lecturas_deposito (deposito, medido_en desc);

-- ---------------------------------------------------------------------------
-- COMANDOS A ACTUADORES
-- ---------------------------------------------------------------------------

-- Crea la tabla solo si todavía no existe.
create table if not exists public.comandos (
  -- Identificador único del comando (UUID).
  id_comando           uuid primary key,
  -- Zona destino.
  zona                 text not null check (zona in ('arida', 'humeda', 'selvatica')),
  -- Actuador destino.
  actuador             text not null check (actuador in ('bomba', 'ventilador', 'luces')),
  -- Estado que se pidió. Pedirlo NO significa que el actuador ya lo tenga.
  estado_solicitado    text not null check (estado_solicitado in ('encendido', 'apagado')),
  -- Etapa del comando: enviado -> (ejecutado | rechazado | caducado | duplicado) o fallido_envio si no salió.
  estado               text not null check (estado in ('enviado', 'ejecutado', 'rechazado', 'caducado', 'duplicado', 'fallido_envio')),
  -- Instante de la solicitud (UTC).
  solicitado_en        timestamptz not null,
  -- Instante después del cual el comando no debe ejecutarse (UTC).
  caduca_en            timestamptz not null,
  -- Instante en que se entregó al broker (NULL si no salió).
  enviado_en           timestamptz,
  -- Instante en que llegó la confirmación del dispositivo (NULL si aún no llega).
  confirmado_en        timestamptz,
  -- Dispositivo que confirmó.
  dispositivo          text,
  -- "real" o "simulado" según quién confirmó.
  origen_confirmacion  text check (origen_confirmacion in ('real', 'simulado')),
  -- Texto explicativo del resultado (por ejemplo, el motivo de un rechazo).
  detalle              text
);

-- Índice para listar los últimos comandos de una zona.
create index if not exists comandos_zona_solicitado_idx
  on public.comandos (zona, solicitado_en desc);

-- ---------------------------------------------------------------------------
-- SEGURIDAD (RLS)
-- ---------------------------------------------------------------------------

-- Activa Row Level Security: sin políticas, los roles "anon" y "authenticated" NO pueden leer ni escribir nada.
alter table public.lecturas_zona     enable row level security;
alter table public.lecturas_deposito enable row level security;
alter table public.comandos          enable row level security;

-- Las políticas de lectura, los permisos (grants), las funciones de ingesta y la publicación en Realtime
-- están en 0002_ingesta_y_tiempo_real.sql.
