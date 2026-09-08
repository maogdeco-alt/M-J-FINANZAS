-- ============================================================================
-- Radicados Semanales · REGLAS DEL ÁREA DE MASIVAS  (una sola vez, compartidas)
--
-- Por qué existe esta tabla:
--   La app es del área de Masivas y la usan cuatro personas. Las reglas con las
--   que se arma la masiva no son una preferencia de cada quien: son las reglas
--   del área. Hasta ahora vivían en el navegador de cada persona, así que cada
--   computador podía estar aplicando reglas distintas sin que nadie lo notara —
--   exactamente el descuadre que se quiere evitar.
--
--   A diferencia de radicados_datos (donde el trabajo de cada persona es suyo y
--   nadie más lo ve), aquí hay UNA SOLA FILA que leen y escriben los cuatro. Es
--   deliberado: si dos personas pudieran tener reglas distintas, la tabla no
--   serviría para lo que se hizo.
--
-- Cómo instalar: Supabase → tu proyecto → SQL Editor → New query → pega todo
-- este archivo → Run. Se puede ejecutar varias veces sin romper nada.
--
-- Si NO se ejecuta: la app sigue funcionando igual, con las reglas de fábrica
-- guardadas en cada navegador, y lo dice en la ventana de Reglas. No se rompe.
-- ============================================================================

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
