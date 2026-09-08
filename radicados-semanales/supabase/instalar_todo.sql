-- ============================================================================
-- Radicados Semanales · Área de Masivas
-- INSTALACIÓN COMPLETA DE LA BASE DE DATOS — un solo archivo, de una sola vez
--
-- Cómo se corre:
--   Supabase → tu proyecto → SQL Editor → New query → pega TODO esto → Run.
--
-- Se puede correr aunque ya hayas ejecutado antes el 0001: no borra nada, no
-- duplica nada y no toca los radicados que ya estén guardados. Todo está
-- escrito para poder repetirse sin consecuencias ("create ... if not exists",
-- "drop policy if exists", "on conflict do nothing").
--
-- Qué deja instalado:
--   1. profiles          — nombre y correo de cada cuenta (solo lo ve su dueño)
--   2. radicados_datos   — el trabajo de cada persona (solo lo ve su dueño)
--   3. reglas_masivas    — LAS REGLAS DEL ÁREA, una sola fila que leen y
--                          escriben las cuatro personas. Es lo ÚNICO compartido
--                          de toda la app, y es a propósito: las reglas con las
--                          que se arma la masiva son del área, no de cada quien.
--
-- Si no corres la parte 3, la app sigue funcionando: cada computador usa su
-- propia copia de las reglas y la ventana "Reglas" lo dice en amarillo.
-- ============================================================================

-- ==========================================================================
-- PARTE 1 y 2 — cuentas y trabajo de cada persona (privado)
-- ==========================================================================

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


-- ==========================================================================
-- PARTE 3 — REGLAS DEL ÁREA DE MASIVAS (compartidas por las cuatro)
-- ==========================================================================

create table if not exists public.reglas_masivas (
  -- Una fila y solo una. El id fijo 'masivas' es lo que lo garantiza.
  id text primary key default 'masivas',
  -- Los parámetros de las reglas (qué clasificaciones aplican a cada una).
  params jsonb not null default '{}'::jsonb,
  -- La bitácora: cada cambio con fecha, quién lo hizo y el antes/después.
  -- Solo se añade; la app no borra entradas.
  bitacora jsonb not null default '[]'::jsonb,
  -- Firma del estado de las reglas, para detectar cambios no anotados.
  firma text not null default '',
  actualizado timestamptz not null default now(),
  actualizado_por text not null default '',
  constraint reglas_masivas_fila_unica check (id = 'masivas')
);

-- La fila nace aquí, en la instalación, y no la crea la app. Así no hace falta
-- darle a nadie permiso de insertar: solo de leer y de actualizar la que ya está.
insert into public.reglas_masivas (id) values ('masivas')
  on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Seguridad por fila. Aquí SÍ es compartido, a diferencia del resto de la app:
-- cualquiera de las cuentas del área puede leer las reglas y ajustarlas. Lo que
-- da cuenta de quién hizo qué no es el permiso, sino la bitácora: cada cambio
-- queda con el correo de quien lo hizo, y la app avisa a las demás personas la
-- próxima vez que entren.
--
-- No se concede borrar ni insertar a propósito: la fila no se puede eliminar ni
-- duplicar desde la app, ni por accidente ni con la llave pública de la página.
-- ---------------------------------------------------------------------------
alter table public.reglas_masivas enable row level security;

drop policy if exists "el area lee las reglas" on public.reglas_masivas;
create policy "el area lee las reglas"
  on public.reglas_masivas for select
  using (auth.uid() is not null);

drop policy if exists "el area ajusta las reglas" on public.reglas_masivas;
create policy "el area ajusta las reglas"
  on public.reglas_masivas for update
  using (auth.uid() is not null)
  with check (auth.uid() is not null);
