-- ============================================================================
-- MA|OG · Control de flota — reporte cada 8 días por correo.
--
-- Solo agrega lo mínimo para que la Edge Function "reporte-semanal" sepa
-- qué negocios están al tanto de recibirlo y cuándo fue la última vez que
-- se envió. No toca nada de lo que ya existe.
--
-- Este script se puede correr más de una vez sin romper nada (usa
-- "if not exists" y "drop policy if exists").
--
-- Después de correr esto en el SQL Editor, sigue con la sección 5 de
-- flota/README.md: ahí está el resto (desplegar la función, guardar la
-- llave de Resend, y programar el cron con TU URL de proyecto).
-- ============================================================================

alter table public.negocios
  add column if not exists reporte_activo boolean not null default true;
alter table public.negocios
  add column if not exists reporte_ultimo_envio timestamptz;

comment on column public.negocios.reporte_activo is
  'Si está en true, la función reporte-semanal le manda a este negocio un correo cada 8 días con lo que necesita atención. Se apaga desde Ajustes → Tu negocio, dentro de la app.';
comment on column public.negocios.reporte_ultimo_envio is
  'Cuándo se envió el último reporte por correo de este negocio. La función lo revisa para no mandar dos veces antes de que se cumplan los 8 días.';

-- Hacía falta una política de actualización para "negocios" — antes solo
-- existían las de crear y leer, así que nadie podía cambiar ni siquiera el
-- nombre del negocio desde la app. Se agrega ahora para que Ajustes pueda
-- prender/apagar el reporte (y de paso, cualquier otro campo futuro).
drop policy if exists "actualizar los negocios a los que pertenezco" on public.negocios;
create policy "actualizar los negocios a los que pertenezco"
  on public.negocios for update
  using (id in (select public.mis_negocios()))
  with check (id in (select public.mis_negocios()));
