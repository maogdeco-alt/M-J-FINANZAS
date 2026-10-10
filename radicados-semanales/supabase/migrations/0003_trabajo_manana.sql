-- ============================================================================
-- Radicados Semanales · TRABAJO DE LA MAÑANA (asignaciones de Donina)
--
-- El trabajo se divide en dos bloques:
--   · MAÑANA — el sheet que Donina sube a las 8 a.m. y hay dos horas para
--     completar. Se clasifican los radicados que el modelo no tomó y se
--     revisa uno por uno lo que el modelo sí clasificó.
--   · TARDE — la masiva de siempre. No se toca nada de eso.
--
-- Esta migración añade UNA SOLA COLUMNA a la tabla que ya existe. No borra
-- nada, no cambia ninguna columna anterior y no toca los radicados guardados.
-- Se puede ejecutar varias veces seguidas sin romper nada.
--
-- Cómo instalar: Supabase → tu proyecto → SQL Editor → New query → pega todo
-- este archivo → Run.
--
-- SI NO SE EJECUTA: la app sigue funcionando. El bloque de la mañana guarda en
-- el navegador (como siempre ha hecho la copia local) y lo dice con un aviso
-- amarillo en su propia pantalla. No se rompe nada y no se pierde el trabajo
-- del día; lo único que falta es que ese trabajo viaje de un computador a otro.
-- ============================================================================

alter table public.radicados_datos
  add column if not exists manana jsonb not null default '{}'::jsonb;

comment on column public.radicados_datos.manana is
  'Trabajo de la mañana (asignaciones de Donina): las filas del sheet del día, '
  'con la clasificación puesta y la revisión de lo que clasificó el modelo, '
  'más el historial de días ya cerrados. Es de cada persona, igual que el '
  'resto de la fila: la seguridad por fila (RLS) que ya existe sobre '
  'radicados_datos cubre esta columna sin cambiar ninguna política.';
