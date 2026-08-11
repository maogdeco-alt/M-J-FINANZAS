-- ============================================================================
-- J&M Finanzas · v3: crear/unirse a una Casa mediante una función atómica
-- (RPC), en vez de varias escrituras separadas que dependen cada una de RLS.
--
-- Contexto: en algunos proyectos, la validación de la sesión al insertar
-- directamente en las tablas desde el cliente falla de forma intermitente
-- o persistente (auth.uid() no se resuelve como debería en ese momento
-- puntual), incluso con las políticas correctas. Esta versión mueve toda la
-- creación de una Casa a una sola función seguridad-definer que hace las 4
-- escrituras de un solo golpe, revisando ella misma quién es el usuario
-- (auth.uid()) en vez de depender de que cada tabla lo revise por separado.
-- ============================================================================

create or replace function public.crear_casa(p_nombre text)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare
  v_espacio_id uuid;
  v_codigo text := '';
  v_abc text := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  v_uid uuid := auth.uid();
  i int;
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida (auth.uid() vino vacío). Sal de la app y entra de nuevo.';
  end if;

  insert into public.espacios (tipo, nombre) values ('casa', p_nombre)
  returning id into v_espacio_id;

  insert into public.miembros_espacio (espacio_id, usuario_id, slot, rol)
  values (v_espacio_id, v_uid, 'a', 'propietario');

  insert into public.espacios_datos (espacio_id, estado)
  values (v_espacio_id, '{}'::jsonb);

  for i in 1..6 loop
    v_codigo := v_codigo || substr(v_abc, floor(random()*length(v_abc)+1)::int, 1);
  end loop;

  insert into public.codigos_casa (codigo, nombre_casa, espacio_id, creado_por)
  values (v_codigo, p_nombre, v_espacio_id, v_uid);

  return v_codigo;
end;
$$;
grant execute on function public.crear_casa(text) to authenticated;

create or replace function public.unirse_casa(p_codigo text)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_espacio_id uuid;
  v_uid uuid := auth.uid();
begin
  if v_uid is null then
    raise exception 'No hay una sesión válida (auth.uid() vino vacío). Sal de la app y entra de nuevo.';
  end if;

  update public.codigos_casa
  set estado = 'usado', usado_por = v_uid, usado_en = now()
  where codigo = upper(trim(p_codigo)) and estado = 'pendiente' and creado_por <> v_uid
  returning espacio_id into v_espacio_id;

  if v_espacio_id is null then
    raise exception 'Ese código no existe, ya se usó, o es tuyo.';
  end if;

  insert into public.miembros_espacio (espacio_id, usuario_id, slot, rol)
  values (v_espacio_id, v_uid, 'b', 'miembro');

  return v_espacio_id;
end;
$$;
grant execute on function public.unirse_casa(text) to authenticated;

-- Volver a dejar la política de espacios en su forma segura (por si quedó
-- abierta de alguna prueba anterior) — ya no es tan crítica porque ahora
-- crear_casa/unirse_casa hacen el trabajo pesado sin pasar por ella, pero
-- igual la dejamos correcta para inserciones directas.
drop policy if exists "crear un espacio (el mio personal, o una casa nueva)" on public.espacios;
create policy "crear un espacio (el mio personal, o una casa nueva)"
  on public.espacios for insert with check (auth.uid() is not null);

notify pgrst, 'reload schema';
