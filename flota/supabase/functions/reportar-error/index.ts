// ============================================================================
// MA|OG · Aviso automático cuando algo se rompe
//
// El navegador de quien esté usando la app llama esta función sola, sin que
// nadie tenga que avisar, cuando ocurre un error de JavaScript que nadie
// atrapó. Esta función arma un correo simple con lo que pasó y lo manda por
// Resend — la misma herramienta que ya usa reporte-semanal — a la dirección
// que se configure abajo. Es "mejor esfuerzo" en las dos puntas: si el
// navegador no logra llamarla, no pasa nada (ver index.html); si esta
// función no logra mandar el correo (faltan secretos, Resend falló), tampoco
// se le devuelve un error a quien la llamó — nunca debe generar un segundo
// problema encima del primero.
//
// Variables de entorno que necesita (Project Settings → Edge Functions →
// Secrets, ver flota/README.md sección 5):
//   RESEND_API_KEY              — la misma llave que ya usa reporte-semanal
//   RESEND_FROM     (opcional)  — mismo remitente que reporte-semanal
//   ALERTA_EMAIL                — a qué correo mandar el aviso (el tuyo).
//                                 Si no se configura, la función no manda
//                                 nada — solo responde "ok" sin hacer nada.
//
// Quién puede llamar esta función: cualquiera que traiga la llave pública
// (anon) del proyecto — la misma que ya guarda el navegador para todo lo
// demás. A propósito no exige haber iniciado sesión: un error puede pasar
// ANTES de entrar (en la pantalla de conectar o de iniciar sesión), y ahí
// también hace falta poder avisar.
// ============================================================================

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") || "";
const RESEND_FROM = Deno.env.get("RESEND_FROM") || "MA|OG <onboarding@resend.dev>";
const ALERTA_EMAIL = Deno.env.get("ALERTA_EMAIL") || "";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const esc = (s: unknown) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" } as Record<string, string>)[c]
  );
const corto = (s: unknown, n: number) => String(s ?? "").slice(0, n);

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }

  const responder = (body: Record<string, unknown>) =>
    new Response(JSON.stringify(body), {
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });

  if (!ALERTA_EMAIL || !RESEND_API_KEY) {
    // No configurado todavía — se responde "ok" igual, sin mandar nada, para
    // que el navegador que llamó nunca vea esto como un error propio.
    return responder({ ok: true, enviado: false, motivo: "sin configurar" });
  }

  let datos: Record<string, unknown> = {};
  try {
    datos = await req.json();
  } catch (_e) {
    return responder({ ok: true, enviado: false, motivo: "cuerpo inválido" });
  }

  const mensaje = corto(datos.mensaje, 500) || "(sin mensaje)";
  const detalle = corto(datos.detalle, 1500);
  const pagina = corto(datos.pagina, 200);
  const negocio = corto(datos.negocio, 200);
  const correo = corto(datos.correo, 200);
  const navegador = corto(datos.navegador, 300);
  const cuando = corto(datos.cuando, 60) || new Date().toISOString();

  const html = `
    <div style="font-family:Georgia,serif;font-size:14px;color:#1B1812;line-height:1.5;max-width:600px">
      <h2 style="margin:0 0 10px">⚠️ Un error en MA|OG</h2>
      <p style="margin:0 0 4px"><strong>Mensaje:</strong> ${esc(mensaje)}</p>
      ${negocio ? `<p style="margin:0 0 4px"><strong>Negocio:</strong> ${esc(negocio)}</p>` : ""}
      ${correo ? `<p style="margin:0 0 4px"><strong>Quién estaba conectado:</strong> ${esc(correo)}</p>` : ""}
      ${pagina ? `<p style="margin:0 0 4px"><strong>Página:</strong> ${esc(pagina)}</p>` : ""}
      <p style="margin:0 0 4px"><strong>Cuándo:</strong> ${esc(cuando)}</p>
      ${navegador ? `<p style="margin:0 0 10px;color:#8C8271;font-size:12px">${esc(navegador)}</p>` : ""}
      ${detalle ? `<pre style="background:#F8F6EE;border:1px solid #E3DECE;border-radius:8px;padding:12px;font-size:11.5px;white-space:pre-wrap;word-break:break-word">${esc(detalle)}</pre>` : ""}
    </div>`;

  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        from: RESEND_FROM,
        to: [ALERTA_EMAIL],
        subject: `MA|OG · Se rompió algo${negocio ? " en " + negocio : ""}`,
        html,
      }),
    });
    if (!r.ok) {
      return responder({ ok: true, enviado: false, motivo: `Resend respondió ${r.status}` });
    }
  } catch (e) {
    return responder({ ok: true, enviado: false, motivo: String((e as Error).message || e) });
  }

  return responder({ ok: true, enviado: true });
});
