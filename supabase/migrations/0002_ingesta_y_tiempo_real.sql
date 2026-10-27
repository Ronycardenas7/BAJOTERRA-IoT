-- ============================================================================
-- 0002_ingesta_y_tiempo_real.sql — Opción A (docs/tiempo-real.md): el ESP32 envía directo a Supabase por HTTPS.
--
-- Qué agrega:
--  * Tabla de dispositivos y claves por dispositivo (la clave se guarda solo como hash SHA-256).
--  * Funciones que llama el ESP32 o el simulador con la clave publicable del proyecto + su clave propia:
--      registrar_lectura, comandos_pendientes, confirmar_comando.
--  * Función que llama la web (usuario con sesión iniciada y permiso de operador): solicitar_comando.
--  * Permisos mínimos: nadie inserta directo en las tablas; todo pasa por funciones que validan.
--  * Lectura solo para usuarios con sesión iniciada (RLS) y publicación en Realtime.
-- Requiere 0001_esquema_inicial.sql. Se puede ejecutar varias veces (idempotente).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- ESQUEMA PRIVADO: no está expuesto por la API de Supabase (solo "public" lo está).
-- ---------------------------------------------------------------------------

-- Crea el esquema "privado" si no existe.
create schema if not exists privado;
-- Nadie fuera del dueño (postgres) puede usar el esquema privado.
revoke all on schema privado from public;

-- ---------------------------------------------------------------------------
-- DISPOSITIVOS
-- ---------------------------------------------------------------------------

-- Lista de dispositivos autorizados a enviar datos.
create table if not exists public.dispositivos (
  -- Identificador del dispositivo (minúsculas, números y guiones), por ejemplo "esp32-selvatica-01".
  id               text primary key check (id ~ '^[a-z0-9-]{2,41}$'),
  -- "zona" (mide una zona), "deposito" (mide un depósito) o "simulador" (puede enviar datos SIMULADOS de todas).
  tipo             text not null check (tipo in ('zona', 'deposito', 'simulador')),
  -- Zona o depósito al que pertenece (null para el simulador).
  destino          text,
  -- Texto libre para reconocerlo (por ejemplo "placa del laboratorio").
  descripcion      text,
  -- Última vez que se comunicó (lectura o consulta de órdenes).
  ultima_conexion  timestamptz,
  -- Fecha de alta.
  creado_en        timestamptz not null default now(),
  -- El destino debe coincidir con el tipo.
  constraint dispositivos_destino_valido check (
    (tipo = 'zona' and destino in ('arida', 'humeda', 'selvatica'))
    or (tipo = 'deposito' and destino in ('principal'))
    or (tipo = 'simulador' and destino is null)
  )
);
-- Activa RLS: sin política, nadie lee ni escribe.
alter table public.dispositivos enable row level security;

-- Claves de los dispositivos: SOLO el hash, nunca la clave en texto. Vive en el esquema privado.
create table if not exists privado.claves_dispositivo (
  -- Dispositivo dueño de la clave (si se borra el dispositivo, se borra su clave).
  dispositivo  text primary key references public.dispositivos (id) on delete cascade,
  -- Hash SHA-256 de la clave.
  clave_hash   bytea not null unique,
  -- false = clave revocada (por ejemplo, si se pierde la placa).
  activa       boolean not null default true,
  -- Fecha de creación de la clave.
  creada_en    timestamptz not null default now()
);

-- Usuarios de Supabase Auth que pueden enviar órdenes a los actuadores.
create table if not exists public.operadores (
  -- Identificador del usuario (si se borra el usuario, se borra el permiso).
  usuario    uuid primary key references auth.users (id) on delete cascade,
  -- Fecha en que se dio el permiso.
  creado_en  timestamptz not null default now()
);
-- Activa RLS.
alter table public.operadores enable row level security;

-- Índice para encontrar rápido las órdenes pendientes de una zona.
create index if not exists comandos_pendientes_idx on public.comandos (zona, solicitado_en) where estado = 'enviado';

-- ---------------------------------------------------------------------------
-- FUNCIONES INTERNAS (esquema privado)
-- ---------------------------------------------------------------------------

-- Devuelve el dispositivo dueño de una clave activa, o lanza un error si la clave no sirve.
create or replace function privado.autenticar_dispositivo(p_clave text)
returns public.dispositivos
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Fila del dispositivo encontrado.
  d public.dispositivos;
begin
  -- Busca la clave por su hash SHA-256 (la clave en texto nunca se guarda).
  select disp.* into d
  from public.dispositivos disp
  join privado.claves_dispositivo c on c.dispositivo = disp.id
  where c.activa and c.clave_hash = sha256(convert_to(coalesce(p_clave, ''), 'UTF8'));
  -- Si no hay coincidencia, responde "no autorizado".
  if not found then
    raise exception using errcode = '28000', message = 'clave de dispositivo inválida o revocada';
  end if;
  -- Devuelve el dispositivo.
  return d;
end;
$$;

-- Lee un número de un objeto JSON: null si falta o es null; error si no es un número.
create or replace function privado.numero(p_objeto jsonb, p_clave text)
returns double precision
language plpgsql
immutable
set search_path = ''
as $$
begin
  -- Ausente o null: dato ausente (nunca se convierte en 0).
  if not (p_objeto ? p_clave) or jsonb_typeof(p_objeto -> p_clave) = 'null' then
    return null;
  end if;
  -- Solo se aceptan números JSON (no texto, no booleanos).
  if jsonb_typeof(p_objeto -> p_clave) <> 'number' then
    raise exception using errcode = '22023', message = format('la medición "%s" debe ser un número o null', p_clave);
  end if;
  -- Devuelve el número.
  return (p_objeto ->> p_clave)::double precision;
end;
$$;

-- Lanza un error si el objeto JSON tiene claves que no están en la lista permitida.
create or replace function privado.exigir_claves(p_objeto jsonb, p_permitidas text[], p_nombre text)
returns void
language plpgsql
immutable
set search_path = ''
as $$
declare
  -- Claves que no están permitidas.
  desconocidas text[];
begin
  -- Debe ser un objeto JSON.
  if jsonb_typeof(p_objeto) <> 'object' then
    raise exception using errcode = '22023', message = format('"%s" debe ser un objeto JSON', p_nombre);
  end if;
  -- Junta las claves desconocidas.
  select array_agg(k order by k) into desconocidas
  from jsonb_object_keys(p_objeto) as k
  where k <> all (p_permitidas);
  -- Si hay alguna, rechaza el mensaje.
  if desconocidas is not null then
    raise exception using errcode = '22023', message = format('claves desconocidas en "%s": %s', p_nombre, desconocidas);
  end if;
end;
$$;

-- Da de alta (o renueva la clave de) un dispositivo y devuelve su clave nueva UNA sola vez.
-- Se ejecuta desde el SQL Editor de Supabase; la clave no queda guardada en texto en ningún lugar.
create or replace function privado.crear_dispositivo(p_id text, p_tipo text, p_destino text, p_descripcion text default null)
returns text
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Clave aleatoria: prefijo "bjt_" + 64 caracteres hexadecimales.
  v_clave text := 'bjt_' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');
begin
  -- Crea el dispositivo o actualiza sus datos si ya existía.
  insert into public.dispositivos (id, tipo, destino, descripcion)
  values (p_id, p_tipo, p_destino, p_descripcion)
  on conflict (id) do update set tipo = excluded.tipo, destino = excluded.destino, descripcion = excluded.descripcion;
  -- Guarda el hash de la clave nueva (reemplaza la anterior y la reactiva).
  insert into privado.claves_dispositivo (dispositivo, clave_hash)
  values (p_id, sha256(convert_to(v_clave, 'UTF8')))
  on conflict (dispositivo) do update set clave_hash = excluded.clave_hash, activa = true, creada_en = now();
  -- Devuelve la clave para copiarla al ESP32 o al .env del simulador.
  return v_clave;
end;
$$;

-- Revoca la clave de un dispositivo (deja de poder enviar datos).
create or replace function privado.revocar_dispositivo(p_id text)
returns void
language sql
security definer
set search_path = ''
as $$
  -- Marca la clave como inactiva.
  update privado.claves_dispositivo set activa = false where dispositivo = p_id;
$$;

-- Ninguna función privada se puede llamar desde la API.
revoke all on all functions in schema privado from public;

-- ---------------------------------------------------------------------------
-- FUNCIONES PÚBLICAS PARA DISPOSITIVOS (ESP32 y simulador)
-- ---------------------------------------------------------------------------

-- Guarda una lectura con el mismo formato JSON del contrato (docs/mqtt-topics.md).
create or replace function public.registrar_lectura(p_clave text, p_lectura jsonb)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Dispositivo dueño de la clave.
  d public.dispositivos;
  -- Datos extraídos y validados del mensaje.
  v_id uuid;
  v_origen text;
  v_calidad text;
  v_medido timestamptz;
  v_tipo text;
  v_destino text;
  v_dispositivo text;
  v_mediciones jsonb;
  v_actuadores jsonb;
  -- Filas insertadas (0 = duplicada).
  v_filas integer;
begin
  -- 1) Autentica al dispositivo por su clave.
  d := privado.autenticar_dispositivo(p_clave);
  -- 2) El mensaje debe ser un objeto JSON.
  if jsonb_typeof(p_lectura) is distinct from 'object' then
    raise exception using errcode = '22023', message = 'la lectura debe ser un objeto JSON';
  end if;
  -- 3) Identificador del mensaje (UUID obligatorio): permite descartar repetidos.
  begin
    v_id := (p_lectura ->> 'id_mensaje')::uuid;
  exception when others then
    raise exception using errcode = '22023', message = 'id_mensaje debe ser un UUID';
  end;
  if v_id is null then
    raise exception using errcode = '22023', message = 'falta id_mensaje';
  end if;
  -- 4) Origen: real o simulado. Un simulador nunca puede declarar datos reales.
  v_origen := p_lectura ->> 'origen';
  if v_origen is null or v_origen not in ('real', 'simulado') then
    raise exception using errcode = '22023', message = 'origen debe ser "real" o "simulado"';
  end if;
  if d.tipo = 'simulador' and v_origen <> 'simulado' then
    raise exception using errcode = '22023', message = 'un simulador solo puede enviar datos con origen "simulado"';
  end if;
  -- 5) Calidad declarada.
  v_calidad := p_lectura ->> 'calidad';
  if v_calidad is null or v_calidad not in ('buena', 'dudosa', 'mala') then
    raise exception using errcode = '22023', message = 'calidad debe ser "buena", "dudosa" o "mala"';
  end if;
  -- 6) Fecha de medición en ISO 8601 CON zona horaria (por ejemplo ...Z).
  if coalesce(p_lectura ->> 'medido_en', '') !~ '(Z|[+-][0-9]{2}:?[0-9]{2})$' then
    raise exception using errcode = '22023', message = 'medido_en debe ser ISO 8601 con zona horaria (por ejemplo 2026-10-27T15:04:05Z)';
  end if;
  begin
    v_medido := (p_lectura ->> 'medido_en')::timestamptz;
  exception when others then
    raise exception using errcode = '22023', message = 'medido_en no es una fecha válida';
  end;
  -- Una fecha muy en el futuro indica un reloj sin sincronizar.
  if v_medido > now() + interval '5 minutes' then
    raise exception using errcode = '22023', message = 'medido_en está en el futuro (¿reloj del dispositivo sin sincronizar?)';
  end if;
  -- 7) A qué zona o depósito pertenece la lectura.
  if d.tipo = 'simulador' then
    -- El simulador indica la zona o el depósito en el propio mensaje.
    if p_lectura ? 'zona' then
      v_tipo := 'zona';
      v_destino := p_lectura ->> 'zona';
    elsif p_lectura ? 'deposito' then
      v_tipo := 'deposito';
      v_destino := p_lectura ->> 'deposito';
    else
      raise exception using errcode = '22023', message = 'el simulador debe indicar "zona" o "deposito"';
    end if;
    -- Los dispositivos simulados se llaman "sim-...".
    v_dispositivo := coalesce(p_lectura ->> 'dispositivo', d.id);
    if v_dispositivo !~ '^sim-[a-z0-9-]{1,37}$' then
      raise exception using errcode = '22023', message = 'un dispositivo simulado debe llamarse "sim-..."';
    end if;
  else
    -- Un ESP32 solo escribe en su propia zona o depósito.
    v_tipo := d.tipo;
    v_destino := d.destino;
    v_dispositivo := d.id;
    -- Si el mensaje trae "dispositivo", debe coincidir con el dueño de la clave.
    if p_lectura ? 'dispositivo' and p_lectura ->> 'dispositivo' is distinct from d.id then
      raise exception using errcode = '22023', message = 'el campo dispositivo no coincide con la clave usada';
    end if;
  end if;
  -- 8) Mediciones (objeto JSON; las que faltan se guardan como null).
  v_mediciones := coalesce(p_lectura -> 'mediciones', '{}'::jsonb);
  -- 9) Inserta según el tipo. Los rangos físicos los vigilan las restricciones CHECK de las tablas.
  if v_tipo = 'zona' then
    -- Solo mediciones conocidas.
    perform privado.exigir_claves(v_mediciones, array['temperatura', 'humedad_ambiente', 'humedad_sustrato', 'luz', 'co2', 'radiacion'], 'mediciones');
    -- Estado reportado de los actuadores.
    v_actuadores := coalesce(p_lectura -> 'actuadores', '{}'::jsonb);
    perform privado.exigir_claves(v_actuadores, array['bomba', 'ventilador', 'luces'], 'actuadores');
    -- Inserta; si el id ya existe (mensaje repetido) no hace nada.
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
    -- Solo mediciones conocidas del depósito.
    perform privado.exigir_claves(v_mediciones, array['conductividad_ec', 'nivel_agua', 'agua_disponible'], 'mediciones');
    -- agua_disponible debe ser booleano o null.
    if jsonb_typeof(v_mediciones -> 'agua_disponible') not in ('boolean', 'null') then
      raise exception using errcode = '22023', message = 'agua_disponible debe ser true, false o null';
    end if;
    -- Inserta; si el id ya existe no hace nada.
    insert into public.lecturas_deposito (
      id_mensaje, deposito, dispositivo, origen, medido_en, recibido_en, calidad, conductividad_ec, nivel_agua, agua_disponible
    ) values (
      v_id, v_destino, v_dispositivo, v_origen, v_medido, now(), v_calidad,
      privado.numero(v_mediciones, 'conductividad_ec'), privado.numero(v_mediciones, 'nivel_agua'),
      (v_mediciones ->> 'agua_disponible')::boolean
    ) on conflict (id_mensaje) do nothing;
  end if;
  -- Cuántas filas se insertaron.
  get diagnostics v_filas = row_count;
  -- Registra que el dispositivo se comunicó.
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  -- Responde si se guardó o si era un mensaje repetido.
  return jsonb_build_object('estado', case when v_filas = 1 then 'guardado' else 'duplicado' end, 'id_mensaje', v_id);
end;
$$;

-- Devuelve las órdenes pendientes (no vencidas) para el dispositivo dueño de la clave.
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
  -- Autentica.
  d := privado.autenticar_dispositivo(p_clave);
  -- Registra que el dispositivo se comunicó.
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  -- Órdenes "enviadas", aún vigentes, de su zona (el simulador ve las de todas las zonas). Máximo 10, la más antigua primero.
  return query
    select c.id_comando, c.zona, c.actuador, c.estado_solicitado, c.solicitado_en, c.caduca_en
    from public.comandos c
    where c.estado = 'enviado'
      and c.caduca_en > now()
      and (d.tipo = 'simulador' or (d.tipo = 'zona' and c.zona = d.destino))
    order by c.solicitado_en
    limit 10;
end;
$$;

-- Registra el resultado de una orden. La primera confirmación manda; las siguientes se ignoran.
create or replace function public.confirmar_comando(p_clave text, p_id_comando uuid, p_resultado text, p_origen text, p_detalle text default null)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Dispositivo dueño de la clave.
  d public.dispositivos;
  -- Filas actualizadas (0 = ya estaba confirmada, no existe o no es de su zona).
  v_filas integer;
begin
  -- Autentica.
  d := privado.autenticar_dispositivo(p_clave);
  -- Resultado permitido.
  if p_resultado is null or p_resultado not in ('ejecutado', 'rechazado', 'caducado', 'duplicado') then
    raise exception using errcode = '22023', message = 'resultado debe ser ejecutado, rechazado, caducado o duplicado';
  end if;
  -- Origen permitido; un simulador solo confirma como "simulado".
  if p_origen is null or p_origen not in ('real', 'simulado') or (d.tipo = 'simulador' and p_origen <> 'simulado') then
    raise exception using errcode = '22023', message = 'origen inválido para este dispositivo';
  end if;
  -- Actualiza solo si sigue pendiente y es de su zona.
  update public.comandos c
  set estado = p_resultado,
      confirmado_en = now(),
      dispositivo = case when d.tipo = 'simulador' then 'sim-zona-' || c.zona else d.id end,
      origen_confirmacion = p_origen,
      detalle = left(p_detalle, 200)
  where c.id_comando = p_id_comando
    and c.estado = 'enviado'
    and (d.tipo = 'simulador' or (d.tipo = 'zona' and c.zona = d.destino));
  -- Cuántas filas cambió.
  get diagnostics v_filas = row_count;
  -- Registra que el dispositivo se comunicó.
  update public.dispositivos set ultima_conexion = now() where id = d.id;
  -- Responde si se registró.
  return jsonb_build_object('actualizado', v_filas = 1);
end;
$$;

-- ---------------------------------------------------------------------------
-- FUNCIÓN PÚBLICA PARA LA WEB
-- ---------------------------------------------------------------------------

-- Crea una orden. Solo usuarios con sesión iniciada que estén en la tabla operadores.
create or replace function public.solicitar_comando(p_zona text, p_actuador text, p_estado text)
returns public.comandos
language plpgsql
security definer
set search_path = ''
as $$
declare
  -- Orden creada.
  v_comando public.comandos;
begin
  -- Debe haber sesión y permiso de operador.
  if auth.uid() is null or not exists (select 1 from public.operadores o where o.usuario = auth.uid()) then
    raise exception using errcode = '42501', message = 'tu cuenta no tiene permiso para enviar órdenes';
  end if;
  -- Crea la orden "enviada" (disponible para el dispositivo) con 30 s de vigencia.
  insert into public.comandos (id_comando, zona, actuador, estado_solicitado, estado, solicitado_en, caduca_en, enviado_en)
  values (gen_random_uuid(), p_zona, p_actuador, p_estado, 'enviado', now(), now() + interval '30 seconds', now())
  returning * into v_comando;
  -- Devuelve la orden (la web sigue su estado hasta la confirmación).
  return v_comando;
end;
$$;

-- ---------------------------------------------------------------------------
-- PERMISOS (grants) Y POLÍTICAS (RLS)
-- ---------------------------------------------------------------------------

-- Quita cualquier permiso automático sobre las tablas del proyecto.
revoke all on public.lecturas_zona, public.lecturas_deposito, public.comandos, public.dispositivos, public.operadores from anon, authenticated;
-- Los usuarios con sesión iniciada solo pueden LEER (las escrituras pasan por las funciones).
grant select on public.lecturas_zona, public.lecturas_deposito, public.comandos, public.dispositivos, public.operadores to authenticated;

-- Políticas de lectura (se recrean para que el script sea repetible).
drop policy if exists "lectura con sesion" on public.lecturas_zona;
create policy "lectura con sesion" on public.lecturas_zona for select to authenticated using (true);
drop policy if exists "lectura con sesion" on public.lecturas_deposito;
create policy "lectura con sesion" on public.lecturas_deposito for select to authenticated using (true);
drop policy if exists "lectura con sesion" on public.comandos;
create policy "lectura con sesion" on public.comandos for select to authenticated using (true);
drop policy if exists "lectura con sesion" on public.dispositivos;
create policy "lectura con sesion" on public.dispositivos for select to authenticated using (true);
-- Cada usuario solo ve si él mismo es operador.
drop policy if exists "ver mi permiso" on public.operadores;
create policy "ver mi permiso" on public.operadores for select to authenticated using (usuario = (select auth.uid()));

-- Funciones: se quita el permiso general y se da solo a quien corresponde.
revoke all on function public.registrar_lectura(text, jsonb) from public, anon, authenticated;
revoke all on function public.comandos_pendientes(text) from public, anon, authenticated;
revoke all on function public.confirmar_comando(text, uuid, text, text, text) from public, anon, authenticated;
revoke all on function public.solicitar_comando(text, text, text) from public, anon, authenticated;
-- Los dispositivos llaman con la clave publicable (rol anon) + su clave propia.
grant execute on function public.registrar_lectura(text, jsonb) to anon, authenticated;
grant execute on function public.comandos_pendientes(text) to anon, authenticated;
grant execute on function public.confirmar_comando(text, uuid, text, text, text) to anon, authenticated;
-- Solo usuarios con sesión pueden pedir órdenes (además se exige ser operador).
grant execute on function public.solicitar_comando(text, text, text) to authenticated;

-- ---------------------------------------------------------------------------
-- TIEMPO REAL: publica los cambios de estas tablas a la web (Supabase Realtime).
-- ---------------------------------------------------------------------------
do $$
declare
  -- Tabla a publicar.
  t text;
begin
  -- Recorre las tablas que la web escucha.
  foreach t in array array['lecturas_zona', 'lecturas_deposito', 'comandos'] loop
    -- La agrega solo si todavía no está en la publicación (así el script es repetible).
    if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = t) then
      execute format('alter publication supabase_realtime add table public.%I', t);
    end if;
  end loop;
end;
$$;
