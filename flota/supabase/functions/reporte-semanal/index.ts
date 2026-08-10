// ============================================================================
// MA|OG · Reporte cada 8 días por correo
//
// Se dispara sola (no la abre nadie): un cron de la base de datos la llama
// una vez al día; esta función revisa qué negocios ya llevan 8 días o más
// sin recibir el reporte y les manda uno por correo con lo que necesita
// atención — pagos vencidos, SOAT/tecnomecánica por vencer, y el resumen de
// plata del periodo.
//
// Variables de entorno que necesita (Project Settings → Edge Functions →
// Secrets, ver flota/README.md sección 5):
//   RESEND_API_KEY              — llave de resend.com para enviar el correo
//   RESEND_FROM   (opcional)    — remitente; por defecto usa el dominio de
//                                 pruebas de Resend, que no requiere verificar
//                                 nada propio
//   APP_URL       (opcional)    — URL de Netlify, para el botón "Abrir la app"
// SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY los pone Supabase automáticamente
// en toda función — no hay que configurarlos.
//
// Quién puede llamar esta función: solo quien traiga de Authorization la
// llave service_role del propio proyecto (nunca la lleva el navegador — la
// app solo guarda la llave pública/anon). Es la misma llave que ya exige el
// "Enforce JWT verification" que trae Supabase por defecto, así que sirve
// para las dos cosas: pasar esa verificación Y la propia de acá abajo.
// ============================================================================

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") || "";
const RESEND_FROM = Deno.env.get("RESEND_FROM") || "MA|OG <onboarding@resend.dev>";
const APP_URL = Deno.env.get("APP_URL") || "";

const DIA_MS = 86400000;
const money = (n: number) =>
  "$" + Math.round(n || 0).toLocaleString("es-CO");
const fmtDate = (iso: string) => {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
};
const todayISO = () => new Date().toISOString().slice(0, 10);
const dayDiff = (a: string, b: string) =>
  Math.round(
    (new Date(b + "T00:00:00").getTime() - new Date(a + "T00:00:00").getTime()) / DIA_MS
  );
const esc = (s: unknown) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" } as Record<string, string>)[c]
  );

type Moto = { id: string; placa: string; canon?: number; soat?: string; tecno?: string };
type Conductor = {
  id: string; nombre: string; motoId?: string; estado?: string;
  inicio?: string; licVence?: string;
};
type Pago = { condId: string; valor: number; fecha: string };
type Gasto = { cargo?: string; cat?: string; valor: number; fecha: string };
type Estado = { motos?: Moto[]; conductores?: Conductor[]; pagos?: Pago[]; gastos?: Gasto[] };

const CAT_DEUDA = "Abono a deuda o compra de moto";

function construirResumen(estado: Estado, desdeISO: string) {
  const motos = estado.motos || [];
  const conductores = estado.conductores || [];
  const pagos = estado.pagos || [];
  const gastos = estado.gastos || [];
  const hoy = todayISO();
  const motoById = (id?: string) => motos.find((m) => m.id === id);
  const esActivo = (c: Conductor) =>
    (c.estado || "Activo") === "Activo" && !!c.motoId && !!motoById(c.motoId);

  type Item = { orden: number; tier: "mora" | "due"; frase: string; cuando: string };
  const atencion: Item[] = [];
  const seViene: Item[] = [];

  motos.forEach((m) => {
    ([["El SOAT", m.soat], ["La tecnomecánica", m.tecno]] as const).forEach(([q, f]) => {
      if (!f) return;
      const d = dayDiff(hoy, f);
      if (d > 30) return;
      const frase = `${q} de <b>${esc(m.placa)}</b> ${d < 0 ? `venció hace ${-d} d` : `vence en ${d} d`}`;
      (d < 0 ? atencion : seViene).push({ orden: d, tier: d < 0 ? "mora" : "due", frase, cuando: fmtDate(f) });
    });
  });

  conductores.filter(esActivo).forEach((c) => {
    if (c.licVence) {
      const dl = dayDiff(hoy, c.licVence);
      if (dl <= 30) {
        const frase = `Licencia de <b>${esc(c.nombre)}</b> ${dl < 0 ? `venció hace ${-dl} d` : `vence en ${dl} d`}`;
        (dl < 0 ? atencion : seViene).push({ orden: dl, tier: dl < 0 ? "mora" : "due", frase, cuando: fmtDate(c.licVence) });
      }
    }
    if (c.inicio) {
      const fin = new Date(new Date(c.inicio + "T00:00:00").getTime() + 29 * DIA_MS).toISOString().slice(0, 10);
      const df = dayDiff(hoy, fin);
      if (df <= 10) {
        const frase = `El mes de contrato de <b>${esc(c.nombre)}</b> ${df < 0 ? `venció hace ${-df} d` : `vence en ${df} d`}`;
        (df < 0 ? atencion : seViene).push({ orden: df, tier: df < 0 ? "mora" : "due", frase, cuando: fmtDate(fin) });
      }
    }
    const canon = motoById(c.motoId)?.canon || 0;
    const dias = c.inicio ? Math.max(dayDiff(c.inicio, hoy) + 1, 0) : 0;
    const esperado = dias * canon;
    const pagado = pagos.filter((p) => p.condId === c.id).reduce((a, p) => a + p.valor, 0);
    const saldo = pagado - esperado;
    if (saldo < 0) {
      const m = motoById(c.motoId);
      atencion.push({
        orden: -100000 - -saldo,
        tier: "mora",
        frase: `<b>${esc(c.nombre)}</b> debe ${money(-saldo)}${m ? " de la " + esc(m.placa) : ""}`,
        cuando: `${dias} d de uso`,
      });
    }
  });

  atencion.sort((a, b) => a.orden - b.orden);
  seViene.sort((a, b) => a.orden - b.orden);

  const enRango = (f: string, a: string, b: string) => f && f >= a && f <= b;
  const ingresos = pagos.filter((p) => enRango(p.fecha, desdeISO, hoy)).reduce((x, p) => x + p.valor, 0);
  const gastosOper = gastos
    .filter((g) => g.cargo === "Empresa" && g.cat !== CAT_DEUDA && enRango(g.fecha, desdeISO, hoy))
    .reduce((x, g) => x + g.valor, 0);
  const pagosPeriodo = pagos.filter((p) => enRango(p.fecha, desdeISO, hoy)).length;

  return { atencion, seViene, ingresos, gastosOper, utilidad: ingresos - gastosOper, pagosPeriodo };
}

function armarCorreoHTML(nombreNegocio: string, desdeISO: string, r: ReturnType<typeof construirResumen>) {
  const item = (it: { frase: string; cuando: string }, color: string) =>
    `<tr><td style="padding:7px 0;border-bottom:1px solid #E3DECE;font-size:14px;color:#1B1812">${it.frase}</td>
     <td style="padding:7px 0;border-bottom:1px solid #E3DECE;font-size:12px;color:${color};text-align:right;white-space:nowrap">${esc(it.cuando)}</td></tr>`;
  const seccion = (titulo: string, items: { frase: string; cuando: string }[], color: string) =>
    !items.length ? "" : `
    <h3 style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#8C8271;margin:22px 0 6px">${titulo}</h3>
    <table style="width:100%;border-collapse:collapse">${items.map((it) => item(it, color)).join("")}</table>`;

  const boton = APP_URL
    ? `<p style="margin:26px 0 0"><a href="${esc(APP_URL)}" style="background:#DD4B22;color:#fff;text-decoration:none;padding:11px 22px;border-radius:999px;font-weight:600;font-size:13.5px;display:inline-block">Abrir la app →</a></p>`
    : "";

  return `<div style="font-family:Georgia,'Iowan Old Style',serif;max-width:560px;margin:0 auto;padding:8px">
    <p style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#8C8271;margin:0 0 4px">MA|OG · ${esc(nombreNegocio)}</p>
    <h1 style="font-size:22px;margin:0 0 4px;font-weight:600">Cómo va el negocio</h1>
    <p style="font-size:13px;color:#5B5344;margin:0 0 18px">Del ${fmtDate(desdeISO)} a hoy, ${fmtDate(todayISO())}.</p>

    <table style="width:100%;border-collapse:collapse;background:#F8F6EE;border-radius:8px;overflow:hidden">
      <tr>
        <td style="padding:14px 16px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8C8271">Recaudado</td>
        <td style="padding:14px 16px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8C8271">Gastos</td>
        <td style="padding:14px 16px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8C8271">Utilidad</td>
      </tr>
      <tr>
        <td style="padding:0 16px 14px;font-size:18px;font-weight:600">${money(r.ingresos)}</td>
        <td style="padding:0 16px 14px;font-size:18px;font-weight:600">${money(r.gastosOper)}</td>
        <td style="padding:0 16px 14px;font-size:18px;font-weight:600;color:${r.utilidad < 0 ? "#9B3324" : "#1B1812"}">${money(r.utilidad)}</td>
      </tr>
    </table>

    ${seccion("Necesita atención", r.atencion, "#9B3324")}
    ${seccion("Se viene pronto", r.seViene, "#8C5A0C")}
    ${!r.atencion.length && !r.seViene.length ? '<p style="margin:22px 0 0;font-size:14px;color:#1B1812">Todo al día — nada vencido ni por vencer en los próximos días. 👍</p>' : ""}

    <p style="margin:22px 0 0;font-size:12.5px;color:#8C8271">${r.pagosPeriodo} pago(s) registrado(s) en el periodo.</p>
    ${boton}
    <p style="margin:28px 0 0;font-size:11px;color:#B0A890">Este correo se manda solo cada 8 días. Se puede apagar desde Ajustes → Tu negocio, dentro de la app.</p>
  </div>`;
}

async function obtenerCorreos(supabase: ReturnType<typeof createClient>, negocioId: string) {
  const { data, error } = await supabase
    .from("miembros_negocio")
    .select("profiles(correo)")
    .eq("negocio_id", negocioId);
  if (error) throw error;
  return (data || [])
    .map((m: any) => m.profiles?.correo)
    .filter((c: unknown): c is string => !!c);
}

async function enviarCorreo(destinatarios: string[], asunto: string, html: string) {
  if (!RESEND_API_KEY) throw new Error("Falta el secreto RESEND_API_KEY");
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: RESEND_FROM, to: destinatarios, subject: asunto, html }),
  });
  if (!r.ok) throw new Error(`Resend respondió ${r.status}: ${await r.text()}`);
}

Deno.serve(async (req) => {
  if (req.headers.get("Authorization") !== `Bearer ${SERVICE_ROLE_KEY}`) {
    return new Response(JSON.stringify({ error: "no autorizado" }), { status: 401 });
  }

  const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
  const ahora = new Date();

  const { data: negocios, error } = await supabase
    .from("negocios")
    .select("id, nombre, reporte_activo, reporte_ultimo_envio")
    .eq("reporte_activo", true);
  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }

  const pendientes = (negocios || []).filter((n: any) => {
    if (!n.reporte_ultimo_envio) return true;
    return (ahora.getTime() - new Date(n.reporte_ultimo_envio).getTime()) / DIA_MS >= 8;
  });

  const resultados: Record<string, unknown>[] = [];
  for (const neg of pendientes as any[]) {
    try {
      const { data: fila, error: e1 } = await supabase
        .from("negocios_datos")
        .select("estado")
        .eq("negocio_id", neg.id)
        .maybeSingle();
      if (e1) throw e1;
      const estado: Estado = (fila?.estado as Estado) || {};

      const desdeISO = neg.reporte_ultimo_envio
        ? String(neg.reporte_ultimo_envio).slice(0, 10)
        : new Date(ahora.getTime() - 8 * DIA_MS).toISOString().slice(0, 10);

      const correos = await obtenerCorreos(supabase, neg.id);
      if (!correos.length) {
        resultados.push({ negocio: neg.nombre, saltado: "sin miembros con correo" });
        continue;
      }

      const resumen = construirResumen(estado, desdeISO);
      const html = armarCorreoHTML(neg.nombre, desdeISO, resumen);
      await enviarCorreo(correos, `MA|OG · Cómo va ${neg.nombre}`, html);

      const { error: e2 } = await supabase
        .from("negocios")
        .update({ reporte_ultimo_envio: ahora.toISOString() })
        .eq("id", neg.id);
      if (e2) throw e2;

      resultados.push({ negocio: neg.nombre, enviado_a: correos.length });
    } catch (e) {
      resultados.push({ negocio: neg.nombre, error: String((e as Error).message || e) });
    }
  }

  return new Response(
    JSON.stringify({ revisados: negocios?.length || 0, procesados: pendientes.length, resultados }),
    { headers: { "Content-Type": "application/json" } }
  );
});
