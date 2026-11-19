-- Habilita los modos de control y conserva las órdenes previas de actuadores.
alter table public.comandos drop constraint if exists comandos_actuador_check;
alter table public.comandos drop constraint if exists comandos_estado_solicitado_check;
alter table public.comandos drop constraint if exists comandos_estado_valido_check;

-- La validación empareja cada tipo de orden con los valores que entiende el Maestro.
alter table public.comandos add constraint comandos_estado_valido_check check (
  (actuador in ('bomba', 'ventilador', 'luces') and estado_solicitado in ('encendido', 'apagado'))
  or (actuador = 'modo' and estado_solicitado in ('manual', 'automatico'))
  or (actuador in ('TOBJ', 'setpoint') and estado_solicitado ~ '^-?[0-9]+(\.[0-9]+)?$')
);

-- PostgREST entrega el objeto JSON completo al parámetro sin nombre del Maestro v3.
create or replace function public.registrar_lectura(jsonb)
returns jsonb
language sql
set search_path = ''
as $$
  select public.registrar_lectura(
    coalesce(nullif(current_setting('request.headers', true), '')::jsonb ->> 'x-device-key', $1 ->> 'p_clave'),
    $1
  );
$$;

-- El Maestro v3 envía un objeto vacío y toma la clave desde la cabecera HTTP.
-- La sobrecarga de cero argumentos conserva el RPC anterior y sus reglas de ámbito y caducidad.
create or replace function public.comandos_pendientes()
returns table (id uuid, zona text, actuador text, estado text)
language sql
set search_path = ''
as $$
  select c.id_comando,
    c.zona,
    case when c.actuador = 'TOBJ' then 'setpoint' else c.actuador end,
    c.estado_solicitado
  from public.comandos_pendientes(nullif(current_setting('request.headers', true), '')::jsonb ->> 'x-device-key') c;
$$;

-- La confirmación del Maestro usa p_id y la misma clave autenticada que la consulta.
create or replace function public.confirmar_comando(p_id uuid)
returns jsonb
language sql
set search_path = ''
as $$
  select public.confirmar_comando(
    nullif(current_setting('request.headers', true), '')::jsonb ->> 'x-device-key',
    p_id,
    'ejecutado',
    'real'
  );
$$;

-- Las funciones nuevas delegan en las funciones existentes que verifican claves de dispositivo.
revoke all on function public.registrar_lectura(jsonb) from public, anon, authenticated;
revoke all on function public.comandos_pendientes() from public, anon, authenticated;
revoke all on function public.confirmar_comando(uuid) from public, anon, authenticated;
grant execute on function public.registrar_lectura(jsonb) to anon, authenticated;
grant execute on function public.comandos_pendientes() to anon, authenticated;
grant execute on function public.confirmar_comando(uuid) to anon, authenticated;

-- Actualiza las firmas disponibles en la API HTTP tras la migración.
notify pgrst, 'reload schema';
