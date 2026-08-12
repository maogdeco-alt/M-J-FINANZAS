-- ============================================================================
-- MA|OG · Control de flota — eliminar un proyecto.
--
-- Antes no había forma de borrar un negocio ya creado, solo salir de la
-- app. Esta función lo permite, pero solo para quien lo creó (rol
-- 'propietario') — quien solo se unió con un código no puede borrar un
-- negocio compartido por error. Borra el negocio y, por las relaciones
-- "on delete cascade" ya definidas en 0001_init.sql, arrastra consigo
-- sus miembros, sus códigos de invitación y todos sus datos
-- (negocios_datos) — no hace falta borrarlos aparte.
--
-- Este script se puede correr más de una vez sin romper nada.
-- ============================================================================

create or replace function public.eliminar_negocio_rpc(p_negocio_id uuid)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_uid uuid := auth.uid();
  v_rol text;
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida — vuelve a entrar con tu correo y contraseña.' using errcode = '28000';
  end if;

  select rol into v_rol from public.miembros_negocio
    where negocio_id = p_negocio_id and usuario_id = v_uid;

  if v_rol is null then
    raise exception 'No perteneces a ese negocio.' using errcode = '42501';
  end if;
  if v_rol <> 'propietario' then
    raise exception 'Solo quien creó el negocio lo puede eliminar.' using errcode = '42501';
  end if;

  delete from public.negocios where id = p_negocio_id;
end;
$$;
grant execute on function public.eliminar_negocio_rpc(uuid) to authenticated;
