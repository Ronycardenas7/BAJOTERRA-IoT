-- ============================================================================
-- 0004_dispositivo_controlador.sql — Una sola placa (ESP32 DevKit) controla las 3 zonas y el depósito.
-- Motivo (D-011): sin sensores inalámbricos, una ESP32 con cable lee las tres zonas. En vez de tres claves (una por
-- zona) se agrega el tipo de dispositivo "controlador": una clave, puede escribir en cualquier zona o depósito
-- (indicándolo en el mensaje con "zona" o "deposito") y ve las órdenes de todas las zonas.
-- A diferencia del "simulador", el controlador SÍ puede enviar origen "real" (hardware) y el campo "dispositivo"
-- siempre es su propio id (no puede hacerse pasar por otro).
-- Requiere 0002. Idempotente.
-- ============================================================================

-- Amplía los tipos permitidos: quita las restricciones antiguas y las crea de nuevo con "controlador".
alter table public.dispositivos drop constraint if exists dispositivos_tipo_check;
alter table public.dispositivos drop constraint if exists dispositivos_destino_valido;
-- Tipos: zona, deposito, simulador o controlador.
alter table public.dispositivos add constraint dispositivos_tipo_check
  check (tipo in ('zona', 'deposito', 'simulador', 'controlador'));
-- El destino debe coincidir con el tipo (simulador y controlador no tienen destino fijo).
alter table public.dispositivos add constraint dispositivos_destino_valido check (
  (tipo = 'zona' and destino in ('arida', 'humeda', 'selvatica'))
  or (tipo = 'deposito' and destino in ('principal'))
  or (tipo in ('simulador', 'controlador') and destino is null)
);

-- Guarda una lectura (misma validación que en 0002, más el tipo "controlador").
create or replace function public.registrar_lectura(p_clave text, p_lectura jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Dispositivo dueño de la clave.
  d public.dispositivos;
  -- Datos extraídos y validados.
  v_id uuid;
  v_origen text;
  v_calidad text;
  v_medido timestamptz;
  v_tipo text;
  v_destino text;
  v_dispositivo text;
  v_mediciones jsonb;
  v_actuadores jsonb;
  -- Filas insertadas (0 = repetida).
  v_filas integer;
begin
  -- 1) Autenticación por clave de dispositivo.
  d := privado.autenticar_dispositivo(p_clave);
  -- 2) Debe ser un objeto JSON.
  if jsonb_typeof(p_lectura) is distinct from 'object' then
    raise exception using errcode = '22023', message = 'la lectura debe ser un objeto JSON';
  end if;
  -- 3) Identificador del mensaje (UUID).
  begin
    v_id := (p_lectura ->> 'id_mensaje')::uuid;
  exception when others then
    raise exception using errcode = '22023', message = 'id_mensaje debe ser un UUID';
  end;
  if v_id is null then
    raise exception using errcode = '22023', message = 'falta id_mensaje';
  end if;
  -- 4) Origen; un simulador nunca declara "real".
  v_origen := p_lectura ->> 'origen';
  if v_origen is null or v_origen not in ('real', 'simulado') then
    raise exception using errcode = '22023', message = 'origen debe ser "real" o "simulado"';
  end if;
  if d.tipo = 'simulador' and v_origen <> 'simulado' then
    raise exception using errcode = '22023', message = 'un simulador solo puede enviar datos con origen "simulado"';
  end if;
  -- 5) Calidad.
  v_calidad := p_lectura ->> 'calidad';
  if v_calidad is null or v_calidad not in ('buena', 'dudosa', 'mala') then
    raise exception using errcode = '22023', message = 'calidad debe ser "buena", "dudosa" o "mala"';
  end if;
  -- 6) Fecha ISO 8601 con zona horaria, no en el futuro.
  if coalesce(p_lectura ->> 'medido_en', '') !~ '(Z|[+-][0-9]{2}:?[0-9]{2})$' then
    raise exception using errcode = '22023', message = 'medido_en debe ser ISO 8601 con zona horaria (por ejemplo 2026-10-27T15:04:05Z)';
  end if;
  begin
    v_medido := (p_lectura ->> 'medido_en')::timestamptz;
  exception when others then
    raise exception using errcode = '22023', message = 'medido_en no es una fecha válida';
  end;
  if v_medido > now() + interval '5 minutes' then
    raise exception using errcode = '22023', message = 'medido_en está en el futuro (¿reloj del dispositivo sin sincronizar?)';
  end if;
  -- 7) Destino de la lectura.
  if d.tipo in ('simulador', 'controlador') then
    -- Simulador y controlador indican la zona o el depósito en el mensaje.
    if p_lectura ? 'zona' then
      v_tipo := 'zona';
      v_destino := p_lectura ->> 'zona';
    elsif p_lectura ? 'deposito' then
      v_tipo := 'deposito';
      v_destino := p_lectura ->> 'deposito';
    else
      raise exception using errcode = '22023', message = 'el mensaje debe indicar "zona" o "deposito"';
    end if;
    if d.tipo = 'simulador' then
      -- El simulador usa nombres "sim-...".
      v_dispositivo := coalesce(p_lectura ->> 'dispositivo', d.id);
      if v_dispositivo !~ '^sim-[a-z0-9-]{1,37}$' then
        raise exception using errcode = '22023', message = 'un dispositivo simulado debe llamarse "sim-..."';
      end if;
    else
      -- El controlador siempre firma con su propio id.
      if p_lectura ? 'dispositivo' and p_lectura ->> 'dispositivo' is distinct from d.id then
        raise exception using errcode = '22023', message = 'el campo dispositivo no coincide con la clave usada';
      end if;
      v_dispositivo := d.id;
    end if;
  else
    -- Dispositivo de una sola zona o depósito.
    v_tipo := d.tipo;
    v_destino := d.destino;
    v_dispositivo := d.id;
    if p_lectura ? 'dispositivo' and p_lectura ->> 'dispositivo' is distinct from d.id then
      raise exception using errcode = '22023', message = 'el campo dispositivo no coincide con la clave usada';
    end if;
  end if;
  -- 8) Mediciones e inserción (los rangos los vigilan las restricciones CHECK).
  v_mediciones := coalesce(p_lectura -> 'mediciones', '{}'::jsonb);
  if v_tipo = 'zona' then
    perform privado.exigir_claves(v_mediciones, array['temperatura', 'humedad_ambiente', 'humedad_sustrato', 'luz', 'co2', 'radiacion'], 'mediciones');
    v_actuadores := coalesce(p_lectura -> 'actuadores', '{}'::jsonb);
    perform privado.exigir_claves(v_actuadores, array['bomba', 'ventilador', 'luces'], 'actuadores');
    insert into public.lecturas_zona (
      id_mensaje, zona, dispositivo, origen, medido_en, recibido_en, calidad,
      temperatura, humedad_ambiente, humedad_sustrato, luz, co2, radiacion,
      bomba, ventilador, luces, modo
    ) values (
      v_id, v_destino, v_dispositivo, v_origen, v_medido, now(), v_calidad,
      privado.numero(v_mediciones, 'temperatura'), privado.numero(v_mediciones, 'humedad_ambiente'),
      privado.numero(v_mediciones, 'humedad_sustrato'), privado.numero(v_mediciones, 'luz'),
      privado.numero(v_mediciones, 'co2'), privado.numero(v_mediciones, 'radiacion'),
      v_actuadores ->> 'bomba', v_actuadores ->> 'ventilador', v_actuadores ->> 'luces', p_lectura ->> 'modo'
    ) on conflict (id_mensaje) do nothing;
  else
    perform privado.exigir_claves(v_mediciones, array['conductividad_ec', 'nivel_agua', 'agua_disponible'], 'mediciones');
    if jsonb_typeof(v_mediciones -> 'agua_disponible') not in ('boolean', 'null') then
      raise exception using errcode = '22023', message = 'agua_disponible debe ser true, false o null';
    end if;
    insert into public.lecturas_deposito (
      id_mensaje, deposito, dispositivo, origen, medido_en, recibido_en, calidad, conductividad_ec, nivel_agua, agua_disponible
    ) values (
      v_id, v_destino, v_dispositivo, v_origen, v_medido, now(), v_calidad,
      privado.numero(v_mediciones, 'conductividad_ec'), privado.numero(v_mediciones, 'nivel_agua'),
      (v_mediciones ->> 'agua_disponible')::boolean
    ) on conflict (id_mensaje) do nothing;
  end if;
  -- 9) Resultado y última conexión.
  get diagnostics v_filas = row_count;
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  return jsonb_build_object('estado', case when v_filas = 1 then 'guardado' else 'duplicado' end, 'id_mensaje', v_id);
end;
$$;

-- Órdenes pendientes: el controlador (como el simulador) ve las de todas las zonas.
create or replace function public.comandos_pendientes(p_clave text)
returns table (id_comando uuid, zona text, actuador text, estado_solicitado text, solicitado_en timestamptz, caduca_en timestamptz)
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Dispositivo dueño de la clave.
  d public.dispositivos;
begin
  -- Autentica y registra la conexión.
  d := privado.autenticar_dispositivo(p_clave);
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  -- Órdenes vigentes de su ámbito (máximo 10, la más antigua primero).
  return query
    select c.id_comando, c.zona, c.actuador, c.estado_solicitado, c.solicitado_en, c.caduca_en
    from public.comandos c
    where c.estado = 'enviado'
      and c.caduca_en > now()
      and (d.tipo in ('simulador', 'controlador') or (d.tipo = 'zona' and c.zona = d.destino))
    order by c.solicitado_en
    limit 10;
end;
$$;

-- Confirmación de órdenes: el controlador confirma con su propio id y puede declarar origen "real".
create or replace function public.confirmar_comando(p_clave text, p_id_comando uuid, p_resultado text, p_origen text, p_detalle text default null)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Dispositivo dueño de la clave.
  d public.dispositivos;
  -- Filas actualizadas.
  v_filas integer;
begin
  -- Autentica.
  d := privado.autenticar_dispositivo(p_clave);
  -- Resultado permitido.
  if p_resultado is null or p_resultado not in ('ejecutado', 'rechazado', 'caducado', 'duplicado') then
    raise exception using errcode = '22023', message = 'resultado debe ser ejecutado, rechazado, caducado o duplicado';
  end if;
  -- Origen permitido; el simulador solo "simulado".
  if p_origen is null or p_origen not in ('real', 'simulado') or (d.tipo = 'simulador' and p_origen <> 'simulado') then
    raise exception using errcode = '22023', message = 'origen inválido para este dispositivo';
  end if;
  -- La primera confirmación manda; solo órdenes de su ámbito.
  update public.comandos c
  set estado = p_resultado,
      confirmado_en = now(),
      dispositivo = case when d.tipo = 'simulador' then 'sim-zona-' || c.zona else d.id end,
      origen_confirmacion = p_origen,
      detalle = left(p_detalle, 200)
  where c.id_comando = p_id_comando
    and c.estado = 'enviado'
    and (d.tipo in ('simulador', 'controlador') or (d.tipo = 'zona' and c.zona = d.destino));
  -- Resultado y última conexión.
  get diagnostics v_filas = row_count;
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  return jsonb_build_object('actualizado', v_filas = 1);
end;
$$;

-- Los permisos de ejecución se conservan con "create or replace", pero se reafirman por claridad.
revoke all on function public.registrar_lectura(text, jsonb) from public, anon, authenticated;
revoke all on function public.comandos_pendientes(text) from public, anon, authenticated;
revoke all on function public.confirmar_comando(text, uuid, text, text, text) from public, anon, authenticated;
grant execute on function public.registrar_lectura(text, jsonb) to anon, authenticated;
grant execute on function public.comandos_pendientes(text) to anon, authenticated;
grant execute on function public.confirmar_comando(text, uuid, text, text, text) to anon, authenticated;
