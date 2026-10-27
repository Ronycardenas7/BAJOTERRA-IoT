-- ============================================================================
-- 0003_hora_servidor.sql — Hora oficial del servidor (UTC).
-- Motivo: un PC con el reloj desfasado (se detectó uno adelantado ~54 min) fecha mal las lecturas del simulador
-- y hace que la web marque como "desactualizados" datos recién llegados. El simulador y la web consultan esta
-- función para calcular su desfase y corregirlo. El ESP32 no la necesita: usa NTP.
-- Idempotente.
-- ============================================================================

-- Devuelve la hora actual del servidor de base de datos (timestamptz, se serializa en UTC).
create or replace function public.hora_servidor()
returns timestamptz
language sql
stable
security invoker
set search_path = ''
as $$
  -- now() es la hora del servidor al inicio de la transacción.
  select now();
$$;

-- Se quita el permiso general y se da solo a los roles de la API (no expone ningún dato).
revoke all on function public.hora_servidor() from public;
grant execute on function public.hora_servidor() to anon, authenticated;
