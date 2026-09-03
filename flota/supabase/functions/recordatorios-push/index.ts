// ============================================================================
// MA|OG · Recordatorios push (avisos en el celular)
//
// Se dispara sola, 3 veces al día: un cron de la base de datos la llama, y
// esta función revisa qué negocios tienen algo pendiente PARA HOY MISMO
// (no lo que se viene en varios días — eso ya lo cubre el reporte cada
// 8 días por correo) y les manda un aviso push a cada celular/navegador que
// se haya suscrito desde Ajustes. Sigue sonando/apareciendo en las
// siguientes corridas mientras lo pendiente siga sin resolverse — el mismo
// gesto de anotar el pago o marcar pagado el fijo es lo que hace que deje
// de avisar, sin ningún botón especial de "ya vi esto".
//
// Qué cuenta como "pendiente hoy":
//   - Motos: un conductor activo sin NINGÚN pago anotado hoy. Solo se
//     revisa en las corridas de la tarde/noche (después de las 6pm hora
//     Colombia) — a mediodía casi ningún conductor ha pagado todavía, y
//     avisar tan temprano sería puro ruido sin utilidad.
//   - Cuentas personales/familia: pagos fijos del mes cuyo día ya llegó (o
//     ya pasó) y no están marcados como pagados; créditos con "avisarme"
//     prendido cuyo día de pago ya llegó (o ya pasó) y no se ha abonado
//     este mes. Estos si se revisan en las 3 corridas del día, porque una
//     cuenta por pagar no depende de la hora, solo de la fecha.
//
// Esta función SOLO LEE negocios_datos, nunca escribe en esa tabla — el
// navegador de quien esté usando la app en ese momento también guarda ahí
// el estado completo del negocio en cada cambio, y si esta función
// también le escribiera (por ejemplo, para "limpiar" una suscripción push
// que ya venció), correría el riesgo de pisar justo un pago que alguien
// acababa de anotar segundos antes. Una suscripción vencida simplemente se
// vuelve a intentar y a descartar en cada corrida — no cuesta nada de más,
// y así el dinero real de la persona nunca queda en riesgo por esto.
//
// Variables de entorno que necesita (Project Settings → Edge Functions →
// Secrets, ver flota/README.md sección 7):
//   VAPID_PRIVATE_KEY           — obligatoria; la llave privada del par
//                                 VAPID (nunca debe estar en el navegador)
//   VAPID_PUBLIC_KEY  (opcional) — por defecto trae la misma que ya está
//                                 metida en la app; solo hace falta tocarla
//                                 si algún día se genera un par nuevo
//   VAPID_SUBJECT     (opcional) — un mailto: o https: de contacto que
//                                 piden los servicios de push; por defecto
//                                 usa un correo genérico de la app
//   APP_URL           (opcional) — URL de Netlify, para que el aviso abra
//                                 la app al tocarlo
// SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY los pone Supabase automáticamente.
//
// Quién puede llamar esta función: solo quien traiga de Authorization la
// llave service_role del propio proyecto — igual que reporte-semanal.
// ============================================================================

import webpush from "npm:web-push@3.6.7";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
// Misma llave pública que trae flota/index.html por defecto (ver VAPID_PUBLIC_KEY
// dentro del archivo) — así, con solo guardar la privada como secreto, ya
// queda funcionando; no hace falta que Mao copie ni pegue la pública en
// ningún lado.
const VAPID_PUBLIC_KEY = Deno.env.get("VAPID_PUBLIC_KEY") ||
  "BDiqcwFXAc3DZJV9az92qsmspSrWd2Ul8YTLIk5tS-WyirbjJXGGRS_ag0tHXT4IixlJ9tJCFXWKRq2FSdpn2wk";
const VAPID_PRIVATE_KEY = Deno.env.get("VAPID_PRIVATE_KEY") || "";
const VAPID_SUBJECT = Deno.env.get("VAPID_SUBJECT") || "mailto:soporte@maog.app";
const APP_URL = Deno.env.get("APP_URL") || "";

const todayISO = () => new Date().toISOString().slice(0, 10);

type Moto = { id: string; canon?: number };
type Conductor = { id: string; nombre: string; motoId?: string; estado?: string };
type Pago = { condId?: string; fecha: string };
type Fijo = { id: string; nombre: string; dia?: number; pagadoMes?: string };
type DeudaPersonal = {
  nombre: string; recordatorio?: boolean; diaPago?: number; saldo?: number;
  cuotasTotal?: number; cuotasPagadas?: number; abonadoMes?: string; posponerHasta?: string;
};
type Suscripcion = {
  id: string;
  endpoint: string;
  keys: { p256dh: string; auth: string };
};
type Estado = {
  motos?: Moto[]; conductores?: Conductor[]; pagos?: Pago[];
  fijos?: Fijo[]; deudas?: DeudaPersonal[];
  config?: { pushSubs?: Suscripcion[] };
};

// ---------------------------------------------------------------------------
// Qué está pendiente HOY — mismo criterio que usa la propia app (Tablero,
// estadoConductor(), renderDeudas()) en index.html, pero mirando solo "hoy",
// no "se viene en unos días" (eso es el terreno del reporte por correo).
// ---------------------------------------------------------------------------
function pendientesMotos(estado: Estado, incluirConductoresSinPago: boolean): string[] {
  if (!incluirConductoresSinPago) return [];
  const motos = estado.motos || [];
  const conductores = estado.conductores || [];
  const pagos = estado.pagos || [];
  const hoy = todayISO();
  const motoById = (id?: string) => motos.find((m) => m.id === id);
  const esActivo = (c: Conductor) => (c.estado || "Activo") === "Activo" && !!c.motoId && !!motoById(c.motoId);
  return conductores
    .filter(esActivo)
    .filter((c) => !pagos.some((p) => p.condId === c.id && p.fecha === hoy))
    .map((c) => `el pago de ${c.nombre}`);
}

function pendientesPersonal(estado: Estado): string[] {
  const diaHoy = new Date().getDate();
  const mesActual = todayISO().slice(0, 7);
  const hoy = todayISO();
  const items: string[] = [];

  (estado.fijos || []).forEach((f) => {
    if (f.pagadoMes === mesActual) return;
    if (typeof f.dia === "number" && f.dia > 0 && f.dia <= diaHoy) items.push(f.nombre);
  });

  const deudaSaldada = (d: DeudaPersonal) => {
    const total = d.cuotasTotal || 0;
    return (d.saldo || 0) <= 0 || (total > 0 && (d.cuotasPagadas || 0) >= total);
  };
  (estado.deudas || []).forEach((d) => {
    if (!d.recordatorio || !d.diaPago) return;
    if (deudaSaldada(d)) return;
    if (d.abonadoMes === mesActual) return;
    if (d.posponerHasta && d.posponerHasta >= hoy) return;
    if (d.diaPago <= diaHoy) items.push(d.nombre);
  });

  return items;
}

function armarAviso(nombreNegocio: string, items: string[]): { titulo: string; cuerpo: string } {
  const titulo = `MA|OG · ${nombreNegocio}`;
  let lista: string;
  if (items.length === 1) {
    lista = items[0];
  } else if (items.length === 2) {
    lista = `${items[0]} y ${items[1]}`;
  } else {
    lista = `${items.slice(0, 2).join(", ")} y ${items.length - 2} más`;
  }
  return { titulo, cuerpo: `Todavía falta anotar ${lista}. Toca para abrirlo.` };
}

Deno.serve(async (req) => {
  if (req.headers.get("Authorization") !== `Bearer ${SERVICE_ROLE_KEY}`) {
    return new Response(JSON.stringify({ error: "no autorizado" }), { status: 401 });
  }
  if (!VAPID_PRIVATE_KEY) {
    return new Response(JSON.stringify({ error: "Falta el secreto VAPID_PRIVATE_KEY" }), { status: 500 });
  }
  webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  // Hora de Colombia (UTC-5 todo el año, sin horario de verano) para decidir
  // si esta corrida en particular ya debe avisar de conductores sin pago.
  const horaColombia = (new Date().getUTCHours() - 5 + 24) % 24;
  const incluirConductoresSinPago = horaColombia >= 18;

  const { data: negocios, error } = await supabase.from("negocios").select("id, nombre, modulos");
  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });

  const resultados: Record<string, unknown>[] = [];

  for (const neg of (negocios || []) as any[]) {
    try {
      const { data: fila, error: e1 } = await supabase
        .from("negocios_datos")
        .select("estado")
        .eq("negocio_id", neg.id)
        .maybeSingle();
      if (e1) throw e1;
      const estado: Estado = (fila?.estado as Estado) || {};

      const suscripciones = estado.config?.pushSubs || [];
      if (!suscripciones.length) {
        resultados.push({ negocio: neg.nombre, saltado: "sin recordatorios activados en ningún celular" });
        continue;
      }

      // Mismo criterio que reporte-semanal para distinguir el tipo de negocio:
      // "motos" no trae modulos.tipo; personal/familia/flexible sí.
      const tipo = neg.modulos?.tipo;
      const esPersonalLike = tipo === "personal" || tipo === "familia";
      const items = esPersonalLike
        ? pendientesPersonal(estado)
        : pendientesMotos(estado, incluirConductoresSinPago);

      if (!items.length) {
        resultados.push({ negocio: neg.nombre, saltado: "nada pendiente hoy" });
        continue;
      }

      const aviso = armarAviso(neg.nombre, items);
      const payload = JSON.stringify({ titulo: aviso.titulo, cuerpo: aviso.cuerpo, url: APP_URL || "/" });

      // Importante: esta función NUNCA escribe en negocios_datos. Esa fila
      // también la guarda el navegador de quien esté usando la app en ese
      // momento (guardando SIEMPRE el estado completo) — si esta función
      // también le escribiera para "limpiar" suscripciones vencidas,
      // corre el riesgo de pisar justo un pago que alguien acababa de
      // anotar segundos antes. Una suscripción vencida (404/410) simplemente
      // se salta en silencio en cada corrida — no cuesta nada intentarla de
      // más, y así el dato real de la persona nunca está en riesgo.
      let enviados = 0;
      for (const sub of suscripciones) {
        try {
          await webpush.sendNotification(
            { endpoint: sub.endpoint, keys: sub.keys },
            payload,
            { TTL: 3 * 60 * 60 }
          );
          enviados++;
        } catch (e: any) {
          if (e?.statusCode === 404 || e?.statusCode === 410) continue; // suscripción vencida: se ignora
          // cualquier otro error (red, servicio caído) tampoco se reintenta acá — la próxima corrida ya lo hace
        }
      }

      resultados.push({ negocio: neg.nombre, pendientes: items.length, avisos_enviados: enviados });
    } catch (e) {
      resultados.push({ negocio: neg.nombre, error: String((e as Error).message || e) });
    }
  }

  return new Response(
    JSON.stringify({ revisados: negocios?.length || 0, hora_colombia: horaColombia, resultados }),
    { headers: { "Content-Type": "application/json" } }
  );
});
