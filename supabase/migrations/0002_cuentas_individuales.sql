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
-- Este script es NUEVO — no depende de 0001_init.sql. Si ya corriste
-- 0001_init.sql en este proyecto y quieres partir de cero, borra esas tablas
-- primero (Table Editor → seleccionar → Delete). Si es un proyecto nuevo,
-- simplemente pega y ejecuta esto en el SQL Editor.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 0. Funciones de apoyo (evitan "infinite recursion" en las políticas RLS
-- cuando una tabla necesita consultarse a sí misma indirectamente).
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
-- 1. Perfiles — uno por cada auth.users (correo + contraseña ya los maneja
--    Supabase Auth; aquí solo guardamos el nombre visible).
-- ---------------------------------------------------------------------------
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null default 'Sin nombre',
  correo text not null,
  creado_en timestamptz not null default now()
);
alter table public.profiles enable row level security;

create policy "ver mi perfil o el de quien comparte un espacio conmigo"
  on public.profiles for select
  using (id = auth.uid() or id in (
    select usuario_id from public.miembros_espacio where espacio_id in (select public.mis_espacios())
  ));
create policy "crear mi propio perfil" on public.profiles for insert with check (id = auth.uid());
create policy "editar mi propio perfil" on public.profiles for update using (id = auth.uid());

-- ---------------------------------------------------------------------------
-- 2. Espacios — 'personal' (uno por usuario, privado) o 'casa' (compartido).
-- ---------------------------------------------------------------------------
create table public.espacios (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('personal','casa')),
  nombre text not null,
  creado_en timestamptz not null default now()
);
alter table public.espacios enable row level security;

create policy "ver los espacios a los que pertenezco"
  on public.espacios for select using (id in (select public.mis_espacios()));
create policy "crear un espacio (el mio personal, o una casa nueva)"
  on public.espacios for insert with check (auth.uid() is not null);

-- ---------------------------------------------------------------------------
-- 3. Miembros de cada espacio. slot 'a'/'b' solo se usa en tipo='casa' — es
--    lo que conecta a cada usuario real con uno de los dos "casilleros" que
--    ya entiende el motor de reparto/aportes/Chanchi de la Casa.
-- ---------------------------------------------------------------------------
create table public.miembros_espacio (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  usuario_id uuid not null references public.profiles(id) on delete cascade,
  slot text check (slot in ('a','b')),
  rol text not null default 'miembro' check (rol in ('propietario','miembro')),
  creado_en timestamptz not null default now(),
  unique (espacio_id, usuario_id),
  unique (espacio_id, slot)
);
alter table public.miembros_espacio enable row level security;

create policy "ver membresias de mis espacios"
  on public.miembros_espacio for select
  using (usuario_id = auth.uid() or espacio_id in (select public.mis_espacios()));

-- Solo te agregas a ti mismo, y solo en dos casos: (a) el espacio todavía no
-- tiene a nadie (lo estás creando tú: tu espacio personal, o el "slot a" de
-- una Casa nueva), o (b) acabas de canjear con éxito un código válido para
-- ese espacio (ver política de codigos_casa más abajo).
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

-- ---------------------------------------------------------------------------
-- 4. Códigos para crear una Casa entre dos personas.
-- ---------------------------------------------------------------------------
create table public.codigos_casa (
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
alter table public.codigos_casa enable row level security;

create policy "ver codigos que cree, que use, o que aun estan pendientes"
  on public.codigos_casa for select
  using (creado_por = auth.uid() or usado_por = auth.uid() or estado = 'pendiente');
create policy "crear un codigo desde un espacio que ya es mio"
  on public.codigos_casa for insert
  with check (creado_por = auth.uid() and espacio_id in (select public.mis_espacios()));
-- Canjear: solo se puede "usar" un código pendiente que no sea el propio, y
-- solo marcándolo usado_por = uno mismo.
create policy "canjear un codigo pendiente de otra persona"
  on public.codigos_casa for update
  using (estado = 'pendiente')
  with check (usado_por = auth.uid() and estado = 'usado' and creado_por <> auth.uid());
-- Revocar: el creador puede cancelar su propio código mientras siga pendiente.
create policy "revocar mi propio codigo sin usar"
  on public.codigos_casa for update
  using (creado_por = auth.uid() and estado = 'pendiente');

-- ---------------------------------------------------------------------------
-- 5. El estado completo de cada espacio (cuentas, movimientos, fijos,
--    deudas, metas, Chanchi... exactamente lo mismo que antes vivía en
--    localStorage, ahora en la nube y por espacio en vez de un solo blob).
-- ---------------------------------------------------------------------------
create table public.espacios_datos (
  espacio_id uuid primary key references public.espacios(id) on delete cascade,
  estado jsonb not null default '{}'::jsonb,
  actualizado timestamptz not null default now()
);
alter table public.espacios_datos enable row level security;

create policy "leer/escribir el estado de mis espacios"
  on public.espacios_datos for all
  using (espacio_id in (select public.mis_espacios()))
  with check (espacio_id in (select public.mis_espacios()));

-- ---------------------------------------------------------------------------
-- 6. Al registrarse alguien nuevo, crear su perfil + su espacio personal
--    automáticamente (igual que en la v1).
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
