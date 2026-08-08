-- ============================================================================
-- J&M Finanzas · v2: cuentas 100% individuales (correo + contraseña) y CASA
-- por código.
--
-- Reemplaza el modelo de "hogares.estado" único compartido (v1, magic link +
-- PIN local) por cuentas reales e independientes. Cada quien se registra con
-- su correo y su contraseña. Al registrarse, automáticamente tiene su propio
-- "espacio personal" (privado, solo suyo). Desde ahí puede crear una "CASA"
-- (genera un código) o unirse a la de alguien más (pega el código que le
-- compartieron). Por ahora una CASA es de exactamente 2 personas — el motor
-- de aportes/reparto/"Entre nosotros" ya está construido así; abrirlo a 3+
-- personas queda para una siguiente fase, marcada al final de este archivo.
--
-- ESTRUCTURA (importante, es lo que se rompió en la versión anterior de este
-- archivo): primero se crean TODAS las tablas, sin ninguna política todavía.
-- Después, ya con todas las tablas existiendo, se agregan todas las
-- políticas de seguridad (RLS). Una política puede necesitar consultar OTRA
-- tabla — por ejemplo, para saber si te puedes unir a una Casa hay que
-- revisar la tabla de códigos —, y si esa tabla todavía no existe en ese
-- punto del script, Postgres lo rechaza y el script se detiene ahí mismo,
-- dejando todo lo de después sin crear. Por eso, en esta versión, ninguna
-- política se escribe hasta que las 5 tablas ya existen.
--
-- Este script es NUEVO — no depende de 0001_init.sql. Si ya corriste una
-- versión anterior de este archivo (0002) y quedó a medias, entra a
-- Table Editor y borra las tablas que hayan quedado (profiles, espacios,
-- miembros_espacio, codigos_casa, espacios_datos) antes de correr esta
-- versión — así no chocas con tablas que ya existan a medias.
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

create table if not exists public.espacios (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('personal','casa')),
  nombre text not null,
  creado_en timestamptz not null default now()
);

-- slot 'a'/'b' solo se usa en tipo='casa' — conecta a cada usuario real con
-- uno de los dos "casilleros" que ya entiende el motor de reparto/aportes/
-- Chanchi de la Casa.
create table if not exists public.miembros_espacio (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  usuario_id uuid not null references public.profiles(id) on delete cascade,
  slot text check (slot in ('a','b')),
  rol text not null default 'miembro' check (rol in ('propietario','miembro')),
  creado_en timestamptz not null default now(),
  unique (espacio_id, usuario_id),
  unique (espacio_id, slot)
);

create table if not exists public.codigos_casa (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique,
  nombre_casa text not null,
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  creado_por uuid not null references public.profiles(id),
  estado text not null default 'pendiente' check (estado in ('pendiente','usado','revocado')),
  usado_por uuid references public.profiles(id),
  creado_en timestamptz not null default now(),
  usado_en timestamptz
);

-- El estado completo de cada espacio (cuentas, movimientos, fijos, deudas,
-- metas, Chanchi... exactamente lo mismo que antes vivía en localStorage,
-- ahora en la nube y por espacio en vez de un solo blob).
create table if not exists public.espacios_datos (
  espacio_id uuid primary key references public.espacios(id) on delete cascade,
  estado jsonb not null default '{}'::jsonb,
  actualizado timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- 2. Activar seguridad por fila (RLS) en las 5 tablas
-- ---------------------------------------------------------------------------
alter table public.profiles enable row level security;
alter table public.espacios enable row level security;
alter table public.miembros_espacio enable row level security;
alter table public.codigos_casa enable row level security;
alter table public.espacios_datos enable row level security;

-- ---------------------------------------------------------------------------
-- 3. Funciones de apoyo para las políticas (ahora sí, con las tablas ya
--    creadas). Evitan "infinite recursion" cuando una política necesita
--    consultar su propia tabla indirectamente.
-- ---------------------------------------------------------------------------
create or replace function public.mis_espacios()
returns setof uuid
language sql security definer stable set search_path = public
as $$
  select espacio_id from public.miembros_espacio where usuario_id = auth.uid();
$$;

create or replace function public.espacio_tiene_miembros(p_espacio_id uuid)
returns boolean
language sql security definer stable set search_path = public
as $$
  select exists(select 1 from public.miembros_espacio where espacio_id = p_espacio_id);
$$;

-- ---------------------------------------------------------------------------
-- 4. Políticas — ya con las 5 tablas y las 2 funciones existiendo, ninguna
--    referencia aquí puede fallar por orden.
-- ---------------------------------------------------------------------------

-- profiles
drop policy if exists "ver mi perfil o el de quien comparte un espacio conmigo" on public.profiles;
create policy "ver mi perfil o el de quien comparte un espacio conmigo"
  on public.profiles for select
  using (id = auth.uid() or id in (
    select usuario_id from public.miembros_espacio where espacio_id in (select public.mis_espacios())
  ));
drop policy if exists "crear mi propio perfil" on public.profiles;
create policy "crear mi propio perfil" on public.profiles for insert with check (id = auth.uid());
drop policy if exists "editar mi propio perfil" on public.profiles;
create policy "editar mi propio perfil" on public.profiles for update using (id = auth.uid());

-- espacios
drop policy if exists "ver los espacios a los que pertenezco" on public.espacios;
create policy "ver los espacios a los que pertenezco"
  on public.espacios for select using (id in (select public.mis_espacios()));
drop policy if exists "crear un espacio (el mio personal, o una casa nueva)" on public.espacios;
create policy "crear un espacio (el mio personal, o una casa nueva)"
  on public.espacios for insert with check (auth.uid() is not null);

-- miembros_espacio
drop policy if exists "ver membresias de mis espacios" on public.miembros_espacio;
create policy "ver membresias de mis espacios"
  on public.miembros_espacio for select
  using (usuario_id = auth.uid() or espacio_id in (select public.mis_espacios()));

-- Solo te agregas a ti mismo, y solo en dos casos: (a) el espacio todavía no
-- tiene a nadie (lo estás creando tú: tu espacio personal, o el "slot a" de
-- una Casa nueva), o (b) acabas de canjear con éxito un código válido para
-- ese espacio.
drop policy if exists "unirme a un espacio (crearlo, o por codigo canjeado)" on public.miembros_espacio;
create policy "unirme a un espacio (crearlo, o por codigo canjeado)"
  on public.miembros_espacio for insert
  with check (
    usuario_id = auth.uid() and (
      not public.espacio_tiene_miembros(espacio_id)
      or exists (
        select 1 from public.codigos_casa cc
        where cc.espacio_id = miembros_espacio.espacio_id
          and cc.usado_por = auth.uid() and cc.estado = 'usado'
      )
    )
  );

-- codigos_casa
drop policy if exists "ver codigos que cree, que use, o que aun estan pendientes" on public.codigos_casa;
create policy "ver codigos que cree, que use, o que aun estan pendientes"
  on public.codigos_casa for select
  using (creado_por = auth.uid() or usado_por = auth.uid() or estado = 'pendiente');
drop policy if exists "crear un codigo desde un espacio que ya es mio" on public.codigos_casa;
create policy "crear un codigo desde un espacio que ya es mio"
  on public.codigos_casa for insert
  with check (creado_por = auth.uid() and espacio_id in (select public.mis_espacios()));
-- Canjear: solo se puede "usar" un código pendiente que no sea el propio, y
-- solo marcándolo usado_por = uno mismo.
drop policy if exists "canjear un codigo pendiente de otra persona" on public.codigos_casa;
create policy "canjear un codigo pendiente de otra persona"
  on public.codigos_casa for update
  using (estado = 'pendiente')
  with check (usado_por = auth.uid() and estado = 'usado' and creado_por <> auth.uid());
-- Revocar: el creador puede cancelar su propio código mientras siga pendiente.
drop policy if exists "revocar mi propio codigo sin usar" on public.codigos_casa;
create policy "revocar mi propio codigo sin usar"
  on public.codigos_casa for update
  using (creado_por = auth.uid() and estado = 'pendiente');

-- espacios_datos
drop policy if exists "leer/escribir el estado de mis espacios" on public.espacios_datos;
create policy "leer/escribir el estado de mis espacios"
  on public.espacios_datos for all
  using (espacio_id in (select public.mis_espacios()))
  with check (espacio_id in (select public.mis_espacios()));

-- ---------------------------------------------------------------------------
-- 5. Al registrarse alguien nuevo, crear su perfil + su espacio personal
--    automáticamente.
-- ---------------------------------------------------------------------------
create or replace function public.manejar_usuario_nuevo()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_espacio_id uuid;
begin
  insert into public.profiles (id, nombre, correo)
  values (new.id, coalesce(new.raw_user_meta_data->>'nombre', split_part(new.email,'@',1)), new.email)
  on conflict (id) do nothing;

  insert into public.espacios (tipo, nombre) values ('personal','Personal') returning id into v_espacio_id;
  insert into public.miembros_espacio (espacio_id, usuario_id, rol) values (v_espacio_id, new.id, 'propietario');
  insert into public.espacios_datos (espacio_id, estado) values (v_espacio_id, '{}'::jsonb);
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute procedure public.manejar_usuario_nuevo();

-- ---------------------------------------------------------------------------
-- Fase siguiente (no incluida aquí a propósito, para no arriesgar esta base):
-- permitir Casas de 3+ personas (familias, roommates) generalizando el
-- slot 'a'/'b' a una lista abierta de miembros, y adaptando el motor de
-- reparto/aportes/Chanchi que hoy asume exactamente dos personas.
-- ---------------------------------------------------------------------------
