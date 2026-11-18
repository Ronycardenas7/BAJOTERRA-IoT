-- ============================================================================
-- 0005_ampliar_comandos_y_maestro_v3.sql — Soporte para órdenes v3.0 y Maestro ESP32
--
-- Motivo:
--  1. Permite cambiar el modo (manual/automatico) y el objetivo de temperatura (TOBJ/setpoint)
--     desde la web y la pantalla a través de la tabla comandos.
--  2. Soporta la llamada directa del Maestro v3.0 por HTTP RPC leyendo la clave de dispositivo
--     tanto desde el cuerpo JSON como desde la cabecera 'x-device-key'.
--  3. Entrega alias 'id' y 'estado' en comandos_pendientes para compatibilidad directa con
--     el deserializador del nuevo Maestro.
--
-- Requiere 0001, 0002 y 0004. Idempotente.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Ampliación de restricciones en la tabla public.comandos
-- ---------------------------------------------------------------------------

-- Quita las restricciones anteriores sobre actuador y estado solicitado.
alter table public.comandos drop constraint if exists comandos_actuador_check;
alter table public.comandos drop constraint if exists comandos_estado_solicitado_check;
alter table public.comandos drop constraint if exists comandos_estado_valido_check;

-- Permite actuadores clásicos (bomba, ventilador, luces) y los nuevos (modo, TOBJ, setpoint).
alter table public.comandos add constraint comandos_actuador_check
  check (actuador in ('bomba', 'ventilador', 'luces', 'modo', 'TOBJ', 'setpoint'));

-- Valida que el estado solicitado coincida con el tipo de actuador:
--  * bomba / ventilador / luces: 'encendido' o 'apagado'
--  * modo: 'manual' o 'automatico'
--  * TOBJ / setpoint: número decimal o entero (ej: '24.5')
alter table public.comandos add constraint comandos_estado_valido_check check (
  (actuador in ('bomba', 'ventilador', 'luces') and estado_solicitado in ('encendido', 'apagado'))
  or (actuador = 'modo' and estado_solicitado in ('manual', 'automatico'))
  or (actuador in ('TOBJ', 'setpoint') and estado_solicitado ~ '^-?[0-9]+(\.[0-9]+)?$')
);

-- ---------------------------------------------------------------------------
-- 2. Sobrecarga de registrar_lectura para objeto único (Prefer: params=single-object)
--    y clave en cabecera 'x-device-key'.
-- ---------------------------------------------------------------------------

create or replace function public.registrar_lectura(p_lectura jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_clave text;
  v_headers json;
begin
  -- Intenta obtener la clave desde la cabecera HTTP 'x-device-key'.
  begin
    v_headers := current_setting('request.headers', true)::json;
    v_clave := v_headers ->> 'x-device-key';
  exception when others then
    v_clave := null;
  end;

  -- Si no vino en cabecera, busca si vino como propiedad en el JSON.
  if v_clave is null then
    v_clave := p_lectura ->> 'p_clave';
  end if;

  -- Delega en la función principal con dos parámetros.
  return public.registrar_lectura(v_clave, p_lectura);
end;
$$;

-- ---------------------------------------------------------------------------
-- 3. Actualización de comandos_pendientes para leer clave en cabecera y devolver alias
-- ---------------------------------------------------------------------------

create or replace function public.comandos_pendientes(p_clave text default null)
returns table (
  id_comando uuid,
  id uuid,
  zona text,
  actuador text,
  estado_solicitado text,
  estado text,
  solicitado_en timestamptz,
  caduca_en timestamptz
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_clave text := p_clave;
  v_headers json;
  d public.dispositivos;
begin
  -- Si no se pasó por parámetro, lee la cabecera 'x-device-key'.
  if v_clave is null or v_clave = '' then
    begin
      v_headers := current_setting('request.headers', true)::json;
      v_clave := v_headers ->> 'x-device-key';
    exception when others then
      v_clave := null;
    end if;
  end if;

  -- Autentica y registra conexión.
  d := privado.autenticar_dispositivo(v_clave);
  update public.dispositivos set ultima_conexion = now() where id = d.id;

  -- Devuelve las órdenes pendientes (máximo 10) con alias id y estado para el Maestro v3.
  return query
    select
      c.id_comando,
      c.id_comando as id,
      c.zona,
      c.actuador,
      c.estado_solicitado,
      c.estado_solicitado as estado,
      c.solicitado_en,
      c.caduca_en
    from public.comandos c
    where c.estado = 'enviado'
      and c.caduca_en > now()
      and (d.tipo in ('simulador', 'controlador') or (d.tipo = 'zona' and c.zona = d.destino))
    order by c.solicitado_en
    limit 10;
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. Actualización de confirmar_comando para aceptar p_id y cabecera 'x-device-key'
-- ---------------------------------------------------------------------------

create or replace function public.confirmar_comando(
  p_id uuid default null,
  p_id_comando uuid default null,
  p_resultado text default 'ejecutado',
  p_origen text default 'real',
  p_detalle text default null,
  p_clave text default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_clave text := p_clave;
  v_id uuid := coalesce(p_id, p_id_comando);
  v_headers json;
  d public.dispositivos;
  v_filas integer;
begin
  -- Si no vino la clave por parámetro, lee la cabecera 'x-device-key'.
  if v_clave is null or v_clave = '' then
    begin
      v_headers := current_setting('request.headers', true)::json;
      v_clave := v_headers ->> 'x-device-key';
    exception when others then
      v_clave := null;
    end if;
  end if;

  -- Autentica el dispositivo.
  d := privado.autenticar_dispositivo(v_clave);

  -- Valida resultado y origen.
  if p_resultado is null or p_resultado not in ('ejecutado', 'rechazado', 'caducado', 'duplicado') then
    raise exception using errcode = '22023', message = 'resultado debe ser ejecutado, rechazado, caducado o duplicado';
  end if;
  if p_origen is null or p_origen not in ('real', 'simulado') or (d.tipo = 'simulador' and p_origen <> 'simulado') then
    raise exception using errcode = '22023', message = 'origen inválido para este dispositivo';
  end if;

  -- Actualiza el estado de la orden.
  update public.comandos c
  set estado = p_resultado,
      confirmado_en = now(),
      dispositivo = case when d.tipo = 'simulador' then 'sim-zona-' || c.zona else d.id end,
      origen_confirmacion = p_origen,
      detalle = left(p_detalle, 200)
  where c.id_comando = v_id
    and c.estado = 'enviado'
    and (d.tipo in ('simulador', 'controlador') or (d.tipo = 'zona' and c.zona = d.destino));

  get diagnostics v_filas = row_count;
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  return jsonb_build_object('actualizado', v_filas = 1);
end;
$$;

-- ---------------------------------------------------------------------------
-- 5. Reafirmar permisos de ejecución para roles anon y authenticated
-- ---------------------------------------------------------------------------

grant execute on function public.registrar_lectura(jsonb) to anon, authenticated;
grant execute on function public.comandos_pendientes(text) to anon, authenticated;
grant execute on function public.confirmar_comando(uuid, uuid, text, text, text, text) to anon, authenticated;
