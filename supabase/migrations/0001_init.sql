-- ============================================================================
-- J&M Finanzas · esquema multiusuario (perfiles independientes + Hogares)
--
-- Reemplaza el modelo anterior de "hogares.estado" (un blob JSON por pareja)
-- por tablas normalizadas: cada persona tiene su propio perfil y su propio
-- espacio personal, y puede pertenecer a cero o varios "Hogares" (espacios
-- compartidos) con distintas personas, sumándose por invitación voluntaria.
--
-- Pensado para correr una sola vez en el SQL editor de un proyecto de
-- Supabase (Database > SQL editor > New query > pegar y ejecutar).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 0. Funciones de apoyo para las políticas (RLS)
--
-- Nota importante: una política RLS sobre "miembros_espacio" NO puede hacer
-- una subconsulta directa contra la propia tabla "miembros_espacio" — eso
-- dispara "infinite recursion detected in policy" en Postgres. Por eso los
-- espacio_id a los que pertenece el usuario se calculan en funciones
-- SECURITY DEFINER: corren con permisos del dueño de la tabla, que no está
-- sujeto a RLS, así que la subconsulta interna no vuelve a evaluar estas
-- mismas políticas.
-- ---------------------------------------------------------------------------
create or replace function public.mis_espacios()
returns setof uuid
language sql
security definer
stable
set search_path = public
as $$
  select espacio_id from public.miembros_espacio
  where usuario_id = auth.uid() and estado = 'activo';
$$;

create or replace function public.mis_espacios_como_propietario()
returns setof uuid
language sql
security definer
stable
set search_path = public
as $$
  select espacio_id from public.miembros_espacio
  where usuario_id = auth.uid() and estado = 'activo' and rol = 'propietario';
$$;

-- Verdad global (sin filtrar por RLS) de si un espacio ya tiene algún
-- miembro. Se usa para distinguir "lo estoy creando yo" de "ya existe y
-- estoy tratando de colarme" en la política de miembros_espacio de abajo —
-- una subconsulta normal contra miembros_espacio ahí solo vería lo que el
-- propio usuario ya puede ver, no la verdad completa de la tabla.
create or replace function public.espacio_tiene_miembros(p_espacio_id uuid)
returns boolean
language sql
security definer
stable
set search_path = public
as $$
  select exists (select 1 from public.miembros_espacio where espacio_id = p_espacio_id);
$$;

-- ---------------------------------------------------------------------------
-- 1. Perfiles (espejo de auth.users, con el nombre visible en la app)
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null default 'Sin nombre',
  correo text not null,
  creado_en timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "ver perfiles de gente con la que comparto un espacio"
  on public.profiles for select
  using (
    id = auth.uid()
    or id in (
      select usuario_id from public.miembros_espacio
      where espacio_id in (select public.mis_espacios())
    )
  );

create policy "crear mi propio perfil"
  on public.profiles for insert
  with check (id = auth.uid());

create policy "editar mi propio perfil"
  on public.profiles for update
  using (id = auth.uid());

-- ---------------------------------------------------------------------------
-- 2. Espacios (personal o Hogar). Un usuario tiene un único espacio
--    'personal'; un Hogar es compartido y nace por invitación aceptada.
-- ---------------------------------------------------------------------------
create table if not exists public.espacios (
  id uuid primary key default gen_random_uuid(),
  tipo text not null check (tipo in ('personal','hogar')),
  nombre text not null,
  creado_en timestamptz not null default now()
);

alter table public.espacios enable row level security;

create policy "ver espacios a los que pertenezco"
  on public.espacios for select
  using (id in (select public.mis_espacios()));

create policy "crear un espacio (personal o Hogar nuevo)"
  on public.espacios for insert
  with check (auth.uid() is not null);

create policy "solo el propietario edita el espacio"
  on public.espacios for update
  using (id in (select public.mis_espacios_como_propietario()));

-- ---------------------------------------------------------------------------
-- 3. Miembros de cada espacio (tabla puente N:M). Aquí vive el "quién
--    pertenece a qué Hogar", el rol y el % de reparto acordado.
-- ---------------------------------------------------------------------------
create table if not exists public.miembros_espacio (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  usuario_id uuid not null references public.profiles(id) on delete cascade,
  rol text not null default 'miembro' check (rol in ('propietario','miembro')),
  estado text not null default 'activo' check (estado in ('activo','salio')),
  reparto_pct numeric,
  creado_en timestamptz not null default now(),
  unique (espacio_id, usuario_id)
);

alter table public.miembros_espacio enable row level security;

create policy "ver membresias de mis espacios"
  on public.miembros_espacio for select
  using (
    usuario_id = auth.uid()
    or espacio_id in (select public.mis_espacios())
  );

-- Solo te puedes agregar a ti mismo, y solo en dos casos: (a) el espacio
-- todavía no tiene ningún miembro (lo estás creando tú) o (b) te llegó una
-- invitación a tu correo para ese espacio. Así nadie se cuela a un Hogar
-- adivinando o compartiendo su id — tiene que haber invitación de por medio.
create policy "unirme yo mismo a un espacio (crear o aceptar invitacion)"
  on public.miembros_espacio for insert
  with check (
    usuario_id = auth.uid()
    and (
      not public.espacio_tiene_miembros(espacio_id)
      or exists (
        select 1 from public.invitaciones i
        where i.espacio_id = miembros_espacio.espacio_id
          and lower(i.para_correo) = lower(auth.jwt() ->> 'email')
      )
    )
  );

create policy "salir de un espacio o cambiar mi reparto"
  on public.miembros_espacio for update
  using (usuario_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 4. Invitaciones. Reemplaza el "pegar el UUID del hogar" del prototipo.
-- ---------------------------------------------------------------------------
create table if not exists public.invitaciones (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  de_usuario_id uuid not null references public.profiles(id),
  para_correo text not null,
  estado text not null default 'pendiente' check (estado in ('pendiente','aceptada','rechazada')),
  creado_en timestamptz not null default now()
);

alter table public.invitaciones enable row level security;

create policy "ver invitaciones que mande o que me llegaron"
  on public.invitaciones for select
  using (
    de_usuario_id = auth.uid()
    or lower(para_correo) = lower(auth.jwt() ->> 'email')
  );

create policy "invitar desde un espacio del que ya soy miembro"
  on public.invitaciones for insert
  with check (
    de_usuario_id = auth.uid()
    and espacio_id in (select public.mis_espacios())
  );

create policy "aceptar/rechazar lo que me invitaron, o cancelar lo que mande"
  on public.invitaciones for update
  using (
    lower(para_correo) = lower(auth.jwt() ->> 'email')
    or de_usuario_id = auth.uid()
  );

-- ---------------------------------------------------------------------------
-- 5. Cuentas bancarias/billeteras, ahora colgadas de un espacio (no de un
--    "bloque" a/b/casa fijo).
-- ---------------------------------------------------------------------------
create table if not exists public.cuentas (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  nombre text not null,
  tipo text not null default 'corriente',
  saldo_inicial numeric not null default 0,
  creado_en timestamptz not null default now()
);

alter table public.cuentas enable row level security;

create policy "solo miembros del espacio ven/gestionan sus cuentas"
  on public.cuentas for all
  using (espacio_id in (select public.mis_espacios()))
  with check (espacio_id in (select public.mis_espacios()));

-- ---------------------------------------------------------------------------
-- 6. Movimientos (ingresos/gastos), colgados de un espacio y de quién los
--    registró.
-- ---------------------------------------------------------------------------
create table if not exists public.movimientos (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  usuario_id uuid not null references public.profiles(id),
  cuenta_id uuid references public.cuentas(id),
  tipo text not null check (tipo in ('ingreso','gasto')),
  monto numeric not null check (monto > 0),
  categoria text,
  descripcion text,
  fecha date not null default current_date,
  creado_en timestamptz not null default now()
);

alter table public.movimientos enable row level security;

create policy "solo miembros activos del espacio ven/gestionan movimientos"
  on public.movimientos for all
  using (espacio_id in (select public.mis_espacios()))
  with check (espacio_id in (select public.mis_espacios()) and usuario_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 7. Préstamos internos ("Entre nosotros") — el cruce de cuentas informal
--    entre miembros de un mismo Hogar.
-- ---------------------------------------------------------------------------
create table if not exists public.prestamos_internos (
  id uuid primary key default gen_random_uuid(),
  espacio_id uuid not null references public.espacios(id) on delete cascade,
  de_usuario_id uuid not null references public.profiles(id),
  para_usuario_id uuid not null references public.profiles(id) check (para_usuario_id <> de_usuario_id),
  monto numeric not null check (monto > 0),
  motivo text,
  fecha date not null default current_date,
  estado text not null default 'pendiente' check (estado in ('pendiente','saldado')),
  creado_en timestamptz not null default now()
);

alter table public.prestamos_internos enable row level security;

create policy "solo miembros activos del espacio ven/gestionan prestamos"
  on public.prestamos_internos for all
  using (espacio_id in (select public.mis_espacios()))
  with check (espacio_id in (select public.mis_espacios()));

-- ---------------------------------------------------------------------------
-- 8. Al registrarse un usuario nuevo (Supabase Auth), crear automáticamente
--    su perfil + su espacio personal + su membresía como propietario. Así la
--    app nunca tiene que "bootstrapear" esto a mano.
-- ---------------------------------------------------------------------------
create or replace function public.manejar_usuario_nuevo()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
  v_espacio_id uuid;
begin
  insert into public.profiles (id, nombre, correo)
  values (new.id, coalesce(split_part(new.email, '@', 1), 'Sin nombre'), new.email)
  on conflict (id) do nothing;

  insert into public.espacios (tipo, nombre)
  values ('personal', 'Personal')
  returning id into v_espacio_id;

  insert into public.miembros_espacio (espacio_id, usuario_id, rol)
  values (v_espacio_id, new.id, 'propietario');

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.manejar_usuario_nuevo();
