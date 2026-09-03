-- ============================================================================
-- MA|OG · Control de flota — plantillas de negocio.
--
-- Hasta ahora cada negocio era, por dentro, siempre el mismo molde: motos,
-- conductores, contratos, pagos y gastos. Este script agrega la columna
-- "plantilla" (motos | flexible) y "modulos" (qué módulos opcionales están
-- prendidos: productos, clientes) a la tabla de negocios, para que una
-- pareja pueda tener proyectos de tipos distintos — uno de renta de
-- vehículos y, aparte, uno de ropa, de servicios, o de puras cuentas
-- personales — cada uno con las herramientas que le sirven.
--
-- No borra ni cambia nada de los negocios que ya existen: a todos les
-- queda "plantilla = 'motos'" por defecto, exactamente como funcionaban
-- antes de este cambio.
--
-- Este script se puede correr más de una vez sin romper nada.
-- ============================================================================

alter table public.negocios add column if not exists plantilla text not null default 'motos';
alter table public.negocios add column if not exists modulos jsonb not null default '{}'::jsonb;

-- ---------------------------------------------------------------------------
-- crear_negocio_rpc ahora también recibe la plantilla elegida y, si es
-- "flexible", qué módulos quedan prendidos (productos, clientes).
-- Se elimina la versión anterior (un solo argumento) para evitar que
-- Postgres se confunda entre las dos firmas.
-- ---------------------------------------------------------------------------
drop function if exists public.crear_negocio_rpc(text);

create or replace function public.crear_negocio_rpc(p_nombre text, p_plantilla text default 'motos', p_modulos jsonb default '{}'::jsonb)
returns table(id uuid, nombre text, codigo text, plantilla text, modulos jsonb)
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_id uuid;
  v_codigo text;
  v_nombre text := coalesce(nullif(trim(p_nombre), ''), 'Mi negocio');
  v_plantilla text := case when p_plantilla = 'flexible' then 'flexible' else 'motos' end;
  v_modulos jsonb := coalesce(p_modulos, '{}'::jsonb);
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;

  insert into public.negocios (nombre, plantilla, modulos) values (v_nombre, v_plantilla, v_modulos) returning negocios.id into v_id;
  insert into public.miembros_negocio (negocio_id, usuario_id, rol) values (v_id, v_uid, 'propietario');
  insert into public.negocios_datos (negocio_id, estado) values (v_id, '{}'::jsonb);
  v_codigo := public.generar_codigo_negocio();
  insert into public.codigos_negocio (codigo, nombre_negocio, negocio_id, creado_por)
    values (v_codigo, v_nombre, v_id, v_uid);

  return query select v_id, v_nombre, v_codigo, v_plantilla, v_modulos;
end;
$$;
grant execute on function public.crear_negocio_rpc(text, text, jsonb) to authenticated;

-- ---------------------------------------------------------------------------
-- mis_negocios_rpc ahora también entrega la plantilla, los módulos y
-- cuántos miembros tiene cada negocio (para mostrar "solo tuyo" o
-- "en pareja" en la lista de Proyectos).
-- ---------------------------------------------------------------------------
drop function if exists public.mis_negocios_rpc();

create or replace function public.mis_negocios_rpc()
returns table(id uuid, nombre text, rol text, reporte_activo boolean, reporte_ultimo_envio timestamptz,
              plantilla text, modulos jsonb, miembros bigint)
language sql security definer set search_path = public stable as $$
  select n.id, n.nombre, m.rol, n.reporte_activo, n.reporte_ultimo_envio, n.plantilla, n.modulos,
    (select count(*) from public.miembros_negocio mm where mm.negocio_id = n.id) as miembros
  from public.miembros_negocio m
  join public.negocios n on n.id = m.negocio_id
  where m.usuario_id = auth.uid();
$$;
grant execute on function public.mis_negocios_rpc() to authenticated;
