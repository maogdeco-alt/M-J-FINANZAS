-- ============================================================================
-- Radicados Semanales · base de datos en la nube (Supabase)
--
-- Cada persona se registra con su correo real de Gmail y una contraseña —
-- eso lo maneja Supabase Auth directamente (no hay contraseñas guardadas a
-- mano en ninguna tabla). Cada quien ve y edita ÚNICAMENTE su propia fila de
-- datos: no hay ningún concepto de "espacio compartido" aquí, a diferencia
-- de otras apps de esta cuenta — el trabajo de cada persona es siempre
-- personal.
--
-- Cómo instalar: Supabase → tu proyecto → SQL Editor → New query → pega todo
-- este archivo → Run.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. TABLAS
-- ---------------------------------------------------------------------------

-- Perfil básico — nombre y correo, visibles solo para su propio dueño.
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null default 'Sin nombre',
  correo text not null,
  creado_en timestamptz not null default now()
);

-- Todo el trabajo de cada persona — radicados, ajustes (incluye alias y
-- nombre para el documento final) e historial de semanas cerradas — en un
-- solo bloque JSON por usuario, igual que antes vivía en localStorage.
create table if not exists public.radicados_datos (
  usuario_id uuid primary key references auth.users(id) on delete cascade,
  records jsonb not null default '[]'::jsonb,
  settings jsonb not null default '{}'::jsonb,
  history jsonb not null default '[]'::jsonb,
  actualizado timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- 2. Seguridad por fila (RLS) — nadie puede leer ni escribir la fila de otra
--    persona, ni con la llave pública (anon key) que queda embebida en la
--    página.
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.radicados_datos enable row level security;

drop policy if exists "ver mi propio perfil" on public.profiles;
create policy "ver mi propio perfil" on public.profiles for select using (id = auth.uid());
drop policy if exists "crear mi propio perfil" on public.profiles;
create policy "crear mi propio perfil" on public.profiles for insert with check (id = auth.uid());
drop policy if exists "editar mi propio perfil" on public.profiles;
create policy "editar mi propio perfil" on public.profiles for update using (id = auth.uid());

drop policy if exists "leer/escribir solo mis propios datos" on public.radicados_datos;
create policy "leer/escribir solo mis propios datos"
  on public.radicados_datos for all
  using (usuario_id = auth.uid())
  with check (usuario_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 3. Al registrarse alguien nuevo: crear su perfil + su fila de datos vacía
--    automáticamente, y EXIGIR que el correo sea de Gmail (regla de negocio
--    de esta entidad — cada cuenta enlazada al Gmail real de la persona).
-- ---------------------------------------------------------------------------
create or replace function public.manejar_usuario_nuevo_radicados()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.email is null or new.email !~* '^[^@\s]+@gmail\.com$' then
    raise exception 'Esta aplicación requiere una cuenta real de Gmail (correo@gmail.com).';
  end if;

  insert into public.profiles (id, nombre, correo)
  values (new.id, coalesce(new.raw_user_meta_data->>'nombre', split_part(new.email,'@',1)), new.email)
  on conflict (id) do nothing;

  insert into public.radicados_datos (usuario_id) values (new.id)
  on conflict (usuario_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created_radicados on auth.users;
create trigger on_auth_user_created_radicados after insert on auth.users
  for each row execute procedure public.manejar_usuario_nuevo_radicados();
