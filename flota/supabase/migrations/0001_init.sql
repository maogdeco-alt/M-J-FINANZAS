-- ============================================================================
-- MA|OG · Control de flota — esquema inicial (cuentas individuales + Negocio
-- por código).
--
-- Pensado para un proyecto de Supabase NUEVO Y SEPARADO del de J&M Finanzas
-- (los datos del negocio de motos — cédulas de conductores, contratos,
-- plata — no se mezclan con las finanzas personales de la casa).
--
-- Mismo modelo que ya funciona en el otro proyecto: cada quien se registra
-- con su correo y su contraseña (cuenta 100% individual). Quien crea el
-- negocio genera un código corto; la otra persona se une pegando ese código.
-- Todo el estado del negocio (motos, conductores, pagos, gastos, cuentas)
-- vive en un solo jsonb por negocio — igual de simple que el prototipo
-- original, solo que ahora protegido por autenticación real en vez de una
-- sola clave compartida.
--
-- ESTRUCTURA (importante, ya se aprendió por las malas en el otro proyecto):
-- primero se crean TODAS las tablas, sin ninguna política todavía. Después,
-- ya con todas las tablas existiendo, se agregan todas las políticas de
-- seguridad (RLS). Una política puede necesitar consultar OTRA tabla, y si
-- esa tabla todavía no existe en ese punto del script, Postgres lo rechaza y
-- el script se detiene ahí mismo, dejando todo lo de después sin crear.
--
-- Este script se puede correr más de una vez sin romper nada (usa
-- "if not exists" y "drop policy if exists" en todas partes).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. TABLAS (todas, sin políticas todavía)
-- ---------------------------------------------------------------------------

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null default 'Sin nombre',
  correo text not null,
  creado_en timestamptz not null default now()
);

-- Un "negocio" = una flota. Normalmente serán ustedes dos, pero no hay límite
-- de miembros por si más adelante suman a alguien (un mecánico, un contador).
create table if not exists public.negocios (
  id uuid primary key default gen_random_uuid(),
  nombre text not null default 'MA|OG',
  creado_en timestamptz not null default now()
);

create table if not exists public.miembros_negocio (
  id uuid primary key default gen_random_uuid(),
  negocio_id uuid not null references public.negocios(id) on delete cascade,
  usuario_id uuid not null references public.profiles(id) on delete cascade,
  rol text not null default 'miembro' check (rol in ('propietario','miembro')),
  creado_en timestamptz not null default now(),
  unique (negocio_id, usuario_id)
);

create table if not exists public.codigos_negocio (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique,
  nombre_negocio text not null,
  negocio_id uuid not null references public.negocios(id) on delete cascade,
  creado_por uuid not null references public.profiles(id),
  estado text not null default 'pendiente' check (estado in ('pendiente','usado','revocado')),
  usado_por uuid references public.profiles(id),
  creado_en timestamptz not null default now(),
  usado_en timestamptz
);

-- El estado completo del negocio: motos, conductores, pagos, gastos, config
-- (dueños, cuenta bancaria, lavadero) — la misma forma que ya usaba el
-- prototipo en localStorage, ahora en la nube y protegida por RLS en vez de
-- una tabla abierta con una sola fila para todo el mundo.
create table if not exists public.negocios_datos (
  negocio_id uuid primary key references public.negocios(id) on delete cascade,
  estado jsonb not null default '{}'::jsonb,
  actualizado timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- 2. Activar seguridad por fila (RLS) en las 5 tablas
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.negocios enable row level security;
alter table public.miembros_negocio enable row level security;
alter table public.codigos_negocio enable row level security;
alter table public.negocios_datos enable row level security;

-- ---------------------------------------------------------------------------
-- 3. Funciones de apoyo para las políticas (ahora sí, con las tablas ya
--    creadas). Evitan "infinite recursion" cuando una política necesita
--    consultar su propia tabla indirectamente.
-- ---------------------------------------------------------------------------
create or replace function public.mis_negocios()
returns setof uuid
language sql security definer stable set search_path = public
as $$
  select negocio_id from public.miembros_negocio where usuario_id = auth.uid();
$$;

create or replace function public.negocio_tiene_miembros(p_negocio_id uuid)
returns boolean
language sql security definer stable set search_path = public
as $$
  select exists(select 1 from public.miembros_negocio where negocio_id = p_negocio_id);
$$;

-- ---------------------------------------------------------------------------
-- 4. Políticas — ya con las 5 tablas y las 2 funciones existiendo, ninguna
--    referencia aquí puede fallar por orden.
-- ---------------------------------------------------------------------------

-- profiles
drop policy if exists "ver mi perfil o el de quien comparte un negocio conmigo" on public.profiles;
create policy "ver mi perfil o el de quien comparte un negocio conmigo"
  on public.profiles for select
  using (id = auth.uid() or id in (
    select usuario_id from public.miembros_negocio where negocio_id in (select public.mis_negocios())
  ));
drop policy if exists "crear mi propio perfil" on public.profiles;
create policy "crear mi propio perfil" on public.profiles for insert with check (id = auth.uid());
drop policy if exists "editar mi propio perfil" on public.profiles;
create policy "editar mi propio perfil" on public.profiles for update using (id = auth.uid());

-- negocios
drop policy if exists "ver los negocios a los que pertenezco" on public.negocios;
create policy "ver los negocios a los que pertenezco"
  on public.negocios for select using (id in (select public.mis_negocios()));
drop policy if exists "crear un negocio nuevo" on public.negocios;
create policy "crear un negocio nuevo"
  on public.negocios for insert with check (auth.uid() is not null);

-- miembros_negocio
drop policy if exists "ver membresias de mis negocios" on public.miembros_negocio;
create policy "ver membresias de mis negocios"
  on public.miembros_negocio for select
  using (usuario_id = auth.uid() or negocio_id in (select public.mis_negocios()));

-- Solo te agregas a ti mismo, y solo en dos casos: (a) el negocio todavía no
-- tiene a nadie (lo estás creando tú, como propietario), o (b) acabas de
-- canjear con éxito un código válido para ese negocio.
drop policy if exists "unirme a un negocio (crearlo, o por codigo canjeado)" on public.miembros_negocio;
create policy "unirme a un negocio (crearlo, o por codigo canjeado)"
  on public.miembros_negocio for insert
  with check (
    usuario_id = auth.uid() and (
      not public.negocio_tiene_miembros(negocio_id)
      or exists (
        select 1 from public.codigos_negocio cn
        where cn.negocio_id = miembros_negocio.negocio_id
          and cn.usado_por = auth.uid() and cn.estado = 'usado'
      )
    )
  );

-- Salir del negocio (por si alguien se equivoca de código o se retira).
drop policy if exists "salirme de un negocio" on public.miembros_negocio;
create policy "salirme de un negocio" on public.miembros_negocio for delete using (usuario_id = auth.uid());

-- codigos_negocio
drop policy if exists "ver codigos que cree, que use, o que aun estan pendientes" on public.codigos_negocio;
create policy "ver codigos que cree, que use, o que aun estan pendientes"
  on public.codigos_negocio for select
  using (creado_por = auth.uid() or usado_por = auth.uid() or estado = 'pendiente');
drop policy if exists "crear un codigo desde un negocio que ya es mio" on public.codigos_negocio;
create policy "crear un codigo desde un negocio que ya es mio"
  on public.codigos_negocio for insert
  with check (creado_por = auth.uid() and negocio_id in (select public.mis_negocios()));
-- Canjear: solo se puede "usar" un código pendiente que no sea el propio, y
-- solo marcándolo usado_por = uno mismo.
drop policy if exists "canjear un codigo pendiente de otra persona" on public.codigos_negocio;
create policy "canjear un codigo pendiente de otra persona"
  on public.codigos_negocio for update
  using (estado = 'pendiente')
  with check (usado_por = auth.uid() and estado = 'usado' and creado_por <> auth.uid());
-- Revocar: el creador puede cancelar su propio código mientras siga pendiente.
drop policy if exists "revocar mi propio codigo sin usar" on public.codigos_negocio;
create policy "revocar mi propio codigo sin usar"
  on public.codigos_negocio for update
  using (creado_por = auth.uid() and estado = 'pendiente');

-- negocios_datos
drop policy if exists "leer/escribir el estado de mis negocios" on public.negocios_datos;
create policy "leer/escribir el estado de mis negocios"
  on public.negocios_datos for all
  using (negocio_id in (select public.mis_negocios()))
  with check (negocio_id in (select public.mis_negocios()));

-- ---------------------------------------------------------------------------
-- 5. Al registrarse alguien nuevo, crear su perfil automáticamente (el
--    negocio no se crea solo — cada quien decide al entrar si crea uno
--    nuevo o se une con un código).
-- ---------------------------------------------------------------------------
create or replace function public.manejar_usuario_nuevo()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, nombre, correo)
  values (new.id, coalesce(new.raw_user_meta_data->>'nombre', split_part(new.email,'@',1)), new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute procedure public.manejar_usuario_nuevo();

-- ---------------------------------------------------------------------------
-- Fin. 5 tablas, RLS en las 5, 2 funciones de apoyo, 1 trigger. Nada más que
-- correr — no depende de ningún otro script ni de las migraciones de la app
-- de finanzas (proyectos de Supabase distintos, bases de datos distintas).
-- ---------------------------------------------------------------------------
