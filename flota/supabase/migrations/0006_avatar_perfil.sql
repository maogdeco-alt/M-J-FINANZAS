-- ============================================================================
-- MA|OG · Control de flota — foto de perfil genérica.
--
-- Cinco íconos para elegir (sol, luna, hoja, ola, estrella) — para
-- diferenciar de un vistazo quién es quién cuando dos personas comparten
-- un negocio. Se guarda en profiles (no en cada negocio) porque es de
-- la CUENTA, no del proyecto: el mismo avatar se ve en todos los
-- negocios a los que se entra.
--
-- Va en profiles.avatar (no en el metadata de auth) a propósito: así lo
-- puede ver cualquiera que comparta un negocio contigo a través de
-- miembros_de_negocio_rpc — si solo viviera en tu sesión, nadie más lo
-- vería nunca, y todo esto es justamente para que se distinga un perfil
-- de otro en la lista de "quiénes tienen acceso".
--
-- Todas las mutaciones pasan por RPC con security definer, nunca por un
-- update directo a la tabla — es el mismo motivo de siempre: el bug ya
-- documentado de Supabase con auth.uid() dentro de políticas RLS en
-- proyectos creados después de octubre de 2025 (ver 0003_rpc_autenticacion.sql).
--
-- Este script se puede correr más de una vez sin romper nada.
-- ============================================================================

alter table public.profiles add column if not exists avatar text not null default 'sol';

comment on column public.profiles.avatar is
  'Uno de 5 avatares genéricos (sol, luna, hoja, ola, estrella) — se elige desde Ajustes.';

-- ---------------------------------------------------------------------------
-- Cambiar mi propio avatar.
-- ---------------------------------------------------------------------------
create or replace function public.actualizar_avatar_rpc(p_avatar text)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;
  if p_avatar not in ('sol','luna','hoja','ola','estrella') then
    raise exception 'Ese avatar no existe.' using errcode = '22023';
  end if;
  update public.profiles set avatar = p_avatar where id = v_uid;
end;
$$;
grant execute on function public.actualizar_avatar_rpc(text) to authenticated;

-- ---------------------------------------------------------------------------
-- Leer mi propio perfil (nombre, correo, avatar) — se llama una vez al
-- entrar, para que la esquina superior muestre el avatar guardado.
-- ---------------------------------------------------------------------------
create or replace function public.mi_perfil_rpc()
returns table(nombre text, correo text, avatar text)
language sql security definer set search_path = public stable as $$
  select nombre, correo, avatar from public.profiles where id = auth.uid();
$$;
grant execute on function public.mi_perfil_rpc() to authenticated;

-- ---------------------------------------------------------------------------
-- miembros_de_negocio_rpc ahora también entrega el avatar de cada quien,
-- para poder mostrarlo en "Quiénes tienen acceso" dentro de Ajustes.
-- ---------------------------------------------------------------------------
drop function if exists public.miembros_de_negocio_rpc(uuid);

create or replace function public.miembros_de_negocio_rpc(p_negocio_id uuid)
returns table(rol text, creado_en timestamptz, nombre text, correo text, avatar text)
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
    select m.rol, m.creado_en, p.nombre, p.correo, p.avatar
    from public.miembros_negocio m
    join public.profiles p on p.id = m.usuario_id
    where m.negocio_id = p_negocio_id;
end;
$$;
grant execute on function public.miembros_de_negocio_rpc(uuid) to authenticated;
