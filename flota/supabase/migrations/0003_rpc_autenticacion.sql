-- ============================================================================
-- MA|OG · Control de flota — funciones RPC para esquivar un problema conocido
-- de Supabase en proyectos nuevos: auth.uid() a veces no se reconoce dentro
-- de una política RLS evaluada sobre una tabla (aunque la sesión sí es
-- válida), pero SÍ se reconoce cuando se llama una función directamente
-- como RPC. Este script mueve cada operación que antes dependía de RLS
-- directo (crear negocio, unirse con código, generar código, leer/guardar
-- los datos del negocio, activar el reporte) a una función con
-- "security definer" que revisa auth.uid() y la membresía a mano, adentro
-- de la función — el mismo nivel de seguridad, en un lugar donde si
-- funciona.
--
-- No reemplaza nada de lo que ya existe (las tablas y políticas de
-- 0001/0002 siguen ahí tal cual, por si en algún momento el problema de
-- Supabase se resuelve solo). Solo agrega estas funciones nuevas.
--
-- Este script se puede correr más de una vez sin romper nada.
-- ============================================================================

create or replace function public.generar_codigo_negocio()
returns text
language sql
as $$
  select string_agg(
    substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', (floor(random()*32)+1)::int, 1), ''
  )
  from generate_series(1,6);
$$;

-- ---------------------------------------------------------------------------
-- Crear un negocio nuevo: negocio + membresía de propietario + fila de datos
-- vacía + código de invitación, todo en una sola operación atómica.
-- ---------------------------------------------------------------------------
create or replace function public.crear_negocio_rpc(p_nombre text)
returns table(id uuid, nombre text, codigo text)
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_id uuid;
  v_codigo text;
  v_nombre text := coalesce(nullif(trim(p_nombre), ''), 'MA|OG');
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;

  insert into public.negocios (nombre) values (v_nombre) returning negocios.id into v_id;
  insert into public.miembros_negocio (negocio_id, usuario_id, rol) values (v_id, v_uid, 'propietario');
  insert into public.negocios_datos (negocio_id, estado) values (v_id, '{}'::jsonb);
  v_codigo := public.generar_codigo_negocio();
  insert into public.codigos_negocio (codigo, nombre_negocio, negocio_id, creado_por)
    values (v_codigo, v_nombre, v_id, v_uid);

  return query select v_id, v_nombre, v_codigo;
end;
$$;
grant execute on function public.crear_negocio_rpc(text) to authenticated;

-- ---------------------------------------------------------------------------
-- Unirse a un negocio existente con un código de 6 letras.
-- ---------------------------------------------------------------------------
create or replace function public.unirse_negocio_rpc(p_codigo text)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_negocio_id uuid;
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;

  update public.codigos_negocio
    set estado = 'usado', usado_por = v_uid, usado_en = now()
    where codigo = upper(trim(p_codigo)) and estado = 'pendiente' and creado_por <> v_uid
    returning negocio_id into v_negocio_id;

  if v_negocio_id is null then
    raise exception 'Ese código no existe, ya se usó, o es tuyo.' using errcode = 'P0002';
  end if;

  insert into public.miembros_negocio (negocio_id, usuario_id, rol)
    values (v_negocio_id, v_uid, 'miembro')
    on conflict (negocio_id, usuario_id) do nothing;

  return v_negocio_id;
end;
$$;
grant execute on function public.unirse_negocio_rpc(text) to authenticated;

-- ---------------------------------------------------------------------------
-- Generar un código de invitación nuevo para un negocio al que ya pertenezco.
-- ---------------------------------------------------------------------------
create or replace function public.generar_codigo_rpc(p_negocio_id uuid)
returns text
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_codigo text;
  v_nombre text;
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if not exists (select 1 from public.miembros_negocio where negocio_id = p_negocio_id and usuario_id = v_uid) then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;

  select nombre into v_nombre from public.negocios where id = p_negocio_id;
  v_codigo := public.generar_codigo_negocio();
  insert into public.codigos_negocio (codigo, nombre_negocio, negocio_id, creado_por)
    values (v_codigo, coalesce(v_nombre,'MA|OG'), p_negocio_id, v_uid);

  return v_codigo;
end;
$$;
grant execute on function public.generar_codigo_rpc(uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- Mis negocios (para la pantalla de entrada y para saber a cuál entrar).
-- ---------------------------------------------------------------------------
create or replace function public.mis_negocios_rpc()
returns table(id uuid, nombre text, rol text, reporte_activo boolean, reporte_ultimo_envio timestamptz)
language sql security definer set search_path = public stable as $$
  select n.id, n.nombre, m.rol, n.reporte_activo, n.reporte_ultimo_envio
  from public.miembros_negocio m
  join public.negocios n on n.id = m.negocio_id
  where m.usuario_id = auth.uid();
$$;
grant execute on function public.mis_negocios_rpc() to authenticated;

-- ---------------------------------------------------------------------------
-- Quiénes tienen acceso a un negocio (pantalla de Ajustes).
-- ---------------------------------------------------------------------------
create or replace function public.miembros_de_negocio_rpc(p_negocio_id uuid)
returns table(rol text, creado_en timestamptz, nombre text, correo text)
language plpgsql security definer set search_path = public stable as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if not exists (select 1 from public.miembros_negocio where negocio_id = p_negocio_id and usuario_id = v_uid) then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;
  return query
    select m.rol, m.creado_en, p.nombre, p.correo
    from public.miembros_negocio m
    join public.profiles p on p.id = m.usuario_id
    where m.negocio_id = p_negocio_id;
end;
$$;
grant execute on function public.miembros_de_negocio_rpc(uuid) to authenticated;

-- ---------------------------------------------------------------------------
-- Leer y guardar el estado del negocio (motos, conductores, pagos, gastos,
-- config) — el corazón de la app, se usa todo el tiempo.
-- ---------------------------------------------------------------------------
create or replace function public.leer_datos_rpc(p_negocio_id uuid)
returns jsonb
language plpgsql security definer set search_path = public stable as $$
declare
  v_uid uuid := auth.uid();
  v_estado jsonb;
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if not exists (select 1 from public.miembros_negocio where negocio_id = p_negocio_id and usuario_id = v_uid) then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;
  select estado into v_estado from public.negocios_datos where negocio_id = p_negocio_id;
  return v_estado;
end;
$$;
grant execute on function public.leer_datos_rpc(uuid) to authenticated;

create or replace function public.guardar_datos_rpc(p_negocio_id uuid, p_estado jsonb)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if not exists (select 1 from public.miembros_negocio where negocio_id = p_negocio_id and usuario_id = v_uid) then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;
  update public.negocios_datos set estado = p_estado, actualizado = now() where negocio_id = p_negocio_id;
end;
$$;
grant execute on function public.guardar_datos_rpc(uuid, jsonb) to authenticated;

-- ---------------------------------------------------------------------------
-- Activar/desactivar el reporte cada 8 días por correo.
-- ---------------------------------------------------------------------------
create or replace function public.actualizar_reporte_rpc(p_negocio_id uuid, p_activo boolean)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if not exists (select 1 from public.miembros_negocio where negocio_id = p_negocio_id and usuario_id = v_uid) then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;
  update public.negocios set reporte_activo = p_activo where id = p_negocio_id;
end;
$$;
grant execute on function public.actualizar_reporte_rpc(uuid, boolean) to authenticated;
