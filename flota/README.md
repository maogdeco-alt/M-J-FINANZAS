# MA|OG · Control de flota

Un solo archivo (`index.html`, sin instalar nada) para llevar el negocio de
comprar motos y alquilarlas: motos, conductores, pagos, gastos, cuánto falta
para recuperar la inversión, y el contrato de arrendamiento listo para
imprimir. Cada uno entra con su propio correo y contraseña — comparten un
mismo "negocio" al que se unen con un código de 6 letras.

Es un proyecto **aparte** de `app/original.html` (las finanzas personales de
la casa): otra base de datos de Supabase, otro sitio de Netlify. Así los
datos del negocio (cédulas de conductores, contratos, plata de la flota) no
se mezclan con las finanzas personales.

## 1. Crear el proyecto de Supabase

1. Entra a [supabase.com](https://supabase.com) y crea un proyecto nuevo
   (gratis) — puede ser el mismo usuario/cuenta que ya usan, simplemente un
   **proyecto distinto** al de las finanzas.
2. **SQL Editor → New query** → pega todo el contenido de
   `flota/supabase/migrations/0001_init.sql` → **Run**.
   (Si el panel se rompe con un error de `removeChild`, ábrelo en una
   ventana de incógnito e inténtalo de nuevo — es un problema del panel de
   Supabase, no del script. El script se puede correr más de una vez sin
   romper nada.)
3. En **Authentication → Providers → Email**, confirma que el login por
   correo esté activo (viene así por defecto). Si quieres que puedan entrar
   apenas se registren, sin confirmar el correo primero, puedes apagar
   "Confirm email" ahí mismo — si lo dejas activo, después de registrarse
   van a tener que abrir un correo de confirmación antes de poder entrar.
4. En **Authentication → URL Configuration**, agrega la URL donde vas a
   publicar la app (la de Netlify, ver el paso 2) en *Site URL* y en
   *Redirect URLs*. Puedes volver a este paso después de publicar.

## 2. Publicar en Netlify (queda conectado — no hay que subir nada a mano)

1. En Netlify: **Add new site → Import an existing project** → elige este
   repositorio de GitHub (`M-J-FINANZAS`).
2. En **Build settings**, configura:
   - **Base directory:** `flota`
   - **Build command:** *(vacío)*
   - **Publish directory:** `flota`
3. Deploy. Cada vez que este repositorio reciba un cambio en la rama
   conectada, Netlify vuelve a publicar solo — no hay que descargar ni
   arrastrar archivos.
4. Copia la URL que te da Netlify (algo como `https://xxxx.netlify.app`) y
   agrégala en Supabase (paso 1.4, *Site URL* y *Redirect URLs*).

## 3. Conectar la app a tu proyecto

1. Abre la URL de Netlify.
2. En la pantalla "Conecta tu base de datos", pega tu **Project URL** y tu
   **llave pública** — están en Supabase, en **Project Settings → API**.
   Según cuándo se creó el proyecto, esa llave se ve distinto: los
   proyectos nuevos muestran `sb_publishable_...`; los más viejos,
   `eyJhbGciOi...` (formato "anon" / JWT). Cualquiera de las dos sirve —
   es la misma llave, Supabase solo cambió cómo se ve. La que **nunca**
   se pega aquí es la que dice `secret` o `service_role` — esa es solo
   para el reporte por correo (sección 5) y no debe salir de ahí.
   Se guardan en este navegador; no hay que repetirlo cada vez.

## 4. Usar la app

1. **Crear cuenta** → tu nombre, tu correo, tu contraseña (mínimo 8
   caracteres, con letras y números). Si el proyecto pide confirmar el
   correo, ábrelo y luego entra con tu clave.
2. La primera persona que entra ve dos opciones: **Crear un negocio** (le
   pone nombre y genera un código de 6 letras) o **Unirme con un
   código** (si su pareja ya lo creó y le compartió el código).
3. Comparte el código por el medio que sea (WhatsApp, de palabra) — sirve
   una sola vez. Si se pierde, se puede generar uno nuevo desde
   **Ajustes → Tu negocio**.
4. Ya adentro, los dos ven y editan la misma información: motos,
   conductores, pagos, gastos, cuentas y contratos.

## 5. Reporte cada 8 días por correo (opcional)

Un correo que llega solo — sin que nadie abra la app — con lo que necesita
atención. El contenido cambia según el tipo de proyecto:

- **Motos**: pagos vencidos, SOAT y tecnomecánica por vencer.
- **Cuentas personales / Cuentas familia**: pagos fijos del mes sin marcar
  como pagados, y las tarjetas de crédito o créditos que se marcaron con
  "Avisarme" y ya están vencidos o por vencer. Si es un proyecto de familia
  y hay un balance entre los dos que valga la pena mencionar, también sale.

En los dos casos trae, además, el resumen de plata del periodo (lo que
entró y lo que salió desde el correo anterior). Es la primera pieza de esta
app que corre en el servidor en vez de en el navegador de quien la usa, así
que tiene más pasos que el resto. Se puede saltar esta sección entera y la
app funciona igual — el reporte es un extra.

Si ya tenías esto configurado de antes (de cuando la app solo tenía
proyectos de motos) y solo quieres que el reporte de tus proyectos de
Cuentas personales/familia empiece a traer los pagos pendientes: no hace
falta repetir todos los pasos. Ve directo a **5.3** y vuelve a pegar el
contenido actualizado de `reporte-semanal/index.ts` sobre la función que ya
existe en Supabase, y dale **Deploy** de nuevo — el resto (secretos, cron,
la migración) sigue igual, no hay que tocarlo.

**5.1 Correr la migración nueva.** SQL Editor → New query → pega todo el
contenido de `flota/supabase/migrations/0002_reporte_periodico.sql` → Run.

**5.2 Crear la cuenta de Resend** (el servicio que manda el correo — no es
de Supabase, es aparte y también gratis para esto).
1. Entra a [resend.com](https://resend.com) y crea una cuenta gratis (100
   correos al día, 3.000 al mes — de sobra para un reporte cada 8 días).
2. En **API Keys**, crea una llave y cópiala — solo se muestra una vez.
3. No hace falta verificar un dominio propio para empezar: Resend deja
   mandar correos desde `onboarding@resend.dev` a cualquier destinatario
   estando en el plan gratis. Si más adelante quieren que el correo llegue
   "de parte de MA|OG" con su propio dominio, se verifica un dominio en
   Resend y se ajusta la variable `RESEND_FROM` (paso 5.4).

**5.3 Desplegar la función** (se pega en el navegador, no hay que instalar
nada en el computador).
1. En el panel de Supabase: **Edge Functions → Create a new function**.
2. Nómbrala `reporte-semanal`.
3. Borra el código de ejemplo y pega todo el contenido de
   `flota/supabase/functions/reporte-semanal/index.ts`.
4. **Deploy**.

**5.4 Guardar los secretos.** Edge Functions → `reporte-semanal` →
Secrets → agrega:
- `RESEND_API_KEY`: la llave del paso 5.2.
- `APP_URL` (opcional): la URL de Netlify (paso 2.4), para que el correo
  traiga un botón "Abrir la app".
- `RESEND_FROM` (opcional): solo si ya verificaron su propio dominio en
  Resend, por ejemplo `MA|OG <reportes@tudominio.com>`.

(La función solo la puede llamar quien traiga la llave `service_role` del
proyecto — nunca la llave pública/anon que usa la app — así que no hace
falta inventar ninguna clave aparte para protegerla.)

**5.5 Programar el envío diario.** Esto necesita la llave `service_role`
de tu proyecto (**Project Settings → API → Project API keys → `service_role`
`secret`**) — es distinta de la llave pública/anon que pegaste en el paso 3;
**no la pongas nunca dentro de la app ni la compartas**, solo va en este
SQL que corres una vez en tu propio proyecto. Para no dejarla escrita en
texto plano, primero se guarda en el *Vault* de Supabase:

```sql
-- 1) Guarda la llave service_role en el Vault (reemplaza el valor).
select vault.create_secret('TU-SERVICE-ROLE-KEY-AQUI', 'reporte_service_key');

-- 2) Programa el cron — reemplaza solo la URL de tu proyecto.
select cron.schedule(
  'reporte-semanal-diario',
  '0 13 * * *', -- 8:00 a.m. hora de Colombia — el cron corre en UTC (UTC-5)
  $$
  select net.http_post(
    url := 'https://TU-PROYECTO.supabase.co/functions/v1/reporte-semanal',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name = 'reporte_service_key'),
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);
```

Si da error de que `cron.schedule`, `net.http_post` o `vault.create_secret`
no existen: **Database → Extensions** → busca `pg_cron`, `pg_net` y
`supabase_vault` → actívalas → corre el SQL de arriba de nuevo.

Esto no manda un correo cada día — corre la función todos los días, y es
la función la que decide, negocio por negocio, si ya pasaron 8 días desde
el último envío. Si un día el cron no corre, no se pierde nada: al otro
día igual detecta que tocaba.

Para probar que quedó bien conectado sin esperar al cron, se puede llamar
la función a mano una vez desde el mismo SQL Editor (el `select net.http_post(...)`
de arriba, sin el `cron.schedule` alrededor) y revisar la respuesta con
`select * from net._http_response order by id desc limit 1;`.

**5.6 Activarlo.** Dentro de la app: **Ajustes → Tu negocio → Reporte cada
8 días por correo**. Viene activado por defecto para negocios nuevos —
llega al correo de cada persona que tenga acceso a ese negocio (los mismos
correos con los que entran a la app). Se apaga desde el mismo lugar.

## 6. Aviso automático si algo se rompe (opcional)

Si a alguien se le rompe la app por un error de JavaScript, esta función te
manda un correo con lo que pasó — sin que esa persona tenga que avisarte.
Usa la misma cuenta de Resend del paso 5.2, así que si ya configuraste el
reporte periódico, este paso es más corto.

**6.1 Desplegar la función.**
1. En el panel de Supabase: **Edge Functions → Create a new function**.
2. Nómbrala `reportar-error`.
3. Borra el código de ejemplo y pega todo el contenido de
   `flota/supabase/functions/reportar-error/index.ts`.
4. **Deploy**.

**6.2 Guardar los secretos.** Edge Functions → `reportar-error` → Secrets
→ agrega:
- `RESEND_API_KEY`: la misma llave del paso 5.2 (si ya la tienes de ahí,
  cópiala tal cual).
- `ALERTA_EMAIL`: el correo tuyo donde quieres recibir estos avisos.
- `RESEND_FROM` (opcional): igual que en el paso 5.4, solo si ya
  verificaron un dominio propio en Resend.

Si te saltas este paso, no pasa nada malo: la app sigue funcionando exactamente
igual, simplemente nadie te avisa por correo si algo se rompe (como es hoy).

(A diferencia del reporte semanal, esta función SÍ la puede llamar el
navegador directamente — con la llave pública/anon de siempre, la misma que
ya usa la app para todo lo demás — porque un error puede pasar antes de que
la persona inicie sesión. No hace falta el paso del `service_role` ni del
cron: el navegador la llama solo, en el momento, cuando algo se rompe.)

## 7. Recordatorios push en el celular (opcional)

Un aviso que aparece directo en el celular — como cualquier notificación de
cualquier otra app, aunque la app esté cerrada del todo — hasta 3 veces al
día si queda algo pendiente por anotar HOY: un conductor que todavía no ha
pagado, un fijo o una cuota que ya llegó su día. Deja de avisar solo, en
cuanto se registra lo que faltaba — no hay ningún botón de "ya vi esto"
aparte, el propio gesto de anotarlo es lo que basta.

Cada celular se suscribe una sola vez desde **Ajustes → Recordatorios en el
celular**; la función revisa 3 veces al día (1pm, 6pm y 11pm hora
Colombia), negocio por negocio, si queda algo pendiente, y si sí, le manda
el aviso a cada celular suscrito de ese negocio.

**Importante en iPhone**: Apple solo permite este tipo de avisos si la app
está **instalada** (ver la sección 4 más arriba, "Instalar la app") —
abrirla desde Safari sin instalar no sirve para esto; la propia app avisa
de esto mismo si lo intentan sin instalarla. En Android/Chrome funciona con
solo abrir el sitio, sin necesidad de instalarlo (aunque instalarlo también
funciona).

**7.1 Sin migración nueva.** Los avisos activados se guardan junto con los
demás datos del negocio, en el mismo lugar de siempre — no hay que correr
ningún SQL nuevo para esta parte.

**7.2 Desplegar la función.**
1. En el panel de Supabase: **Edge Functions → Create a new function**.
2. Nómbrala `recordatorios-push`.
3. Borra el código de ejemplo y pega todo el contenido de
   `flota/supabase/functions/recordatorios-push/index.ts`.
4. **Deploy**.

**7.3 Guardar el secreto.** Edge Functions → `recordatorios-push` →
Secrets → agrega:
- `VAPID_PRIVATE_KEY`: la llave privada del par que identifica a la app
  frente a los servicios de aviso de Google/Apple/Firefox — **nunca va en
  el navegador, solo acá**. Pídesela a Claude en la conversación (ya viene
  generada, junto con su pareja pública que ya está metida en
  `flota/index.html`) — por eso no está escrita en este archivo: un
  secreto de verdad no debe quedar en un repositorio, ni siquiera uno
  propio.

  Si en algún momento prefieres generar tu propio par de llaves nuevo (por
  ejemplo, instalando Node.js y corriendo
  `npx web-push generate-vapid-keys` en una terminal), puedes reemplazar
  esta y también la de abajo — pero no hace falta, la que ya viene sirve
  igual.
- `VAPID_PUBLIC_KEY` (opcional): solo hace falta si generas un par de
  llaves nuevo — en ese caso, también hay que reemplazar el valor de
  `const VAPID_PUBLIC_KEY` dentro de `flota/index.html` por la pública
  nueva, y volver a publicar el sitio; si no, se puede dejar así, ya trae
  la que corresponde por defecto.
- `VAPID_SUBJECT` (opcional): un correo tipo `mailto:tucorreo@gmail.com`
  — algunos de estos servicios lo piden para poder contactarte si algo
  anda mal con los avisos. Si se deja así, usa uno genérico.
- `APP_URL` (opcional): la URL de Netlify, para que al tocar el aviso
  abra la app directo ahí.

**7.4 Programar las 3 corridas diarias.** Necesita la misma llave
`service_role` del paso 5.5 — si ya guardaste ahí el secreto
`reporte_service_key` en el Vault, reutilízalo tal cual, no hace falta
guardarlo de nuevo. Si te saltaste el paso 5.5, primero corre:

```sql
select vault.create_secret('TU-SERVICE-ROLE-KEY-AQUI', 'reporte_service_key');
```

Y luego programa el cron — reemplaza solo la URL de tu proyecto:

```sql
select cron.schedule(
  'recordatorios-push-diario',
  '0 18,23,4 * * *', -- 1pm, 6pm y 11pm hora de Colombia — el cron corre en UTC (UTC-5)
  $$
  select net.http_post(
    url := 'https://TU-PROYECTO.supabase.co/functions/v1/recordatorios-push',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name = 'reporte_service_key'),
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);
```

**7.5 Activarlo.** Dentro de la app, en cada celular donde se quieran
recibir los avisos: **Ajustes → Recordatorios en el celular → Activar en
este celular**. El navegador va a pedir permiso para mostrar
notificaciones — hay que aceptarlo. Se apaga desde el mismo botón, ahí
mismo, solo en ese celular (cada quien activa el suyo).

Para probar que quedó bien conectado sin esperar a que llegue la hora, se
puede llamar la función a mano una vez desde el SQL Editor (el mismo
`select net.http_post(...)` de arriba, sin el `cron.schedule` alrededor) y
revisar la respuesta con
`select * from net._http_response order by id desc limit 1;` — o
directamente en **Edge Functions → recordatorios-push → Logs**, para ver
si encontró algo pendiente y a cuántos celulares les avisó.

## Cómo está pensada la seguridad

- Cada quien tiene su propia cuenta (correo + contraseña) — no hay una sola
  clave compartida como en el borrador inicial.
- La base de datos usa RLS (seguridad por fila): solo quienes pertenecen al
  negocio pueden leer o escribir sus datos — se hace cumplir en la base de
  datos, no solo en la pantalla.
- Cada pago, gasto, moto y conductor que se registra queda con el nombre de
  quién lo registró (se ve en la lista, y también en el Excel exportado).
- La app pide contraseñas de mínimo 8 caracteres con letras y números al
  crear una cuenta — pero esa es solo la primera barrera, del lado del
  navegador. La que de verdad manda es la de Supabase: **Authentication →
  Policies (o Providers) → Minimum password length**. Si tu proyecto es
  viejo y ese número todavía está en 6, vale la pena subirlo a 8 ahí
  también, para que quede protegido incluso si alguien intenta saltarse
  la pantalla de la app.

## Lo que queda por fuera de esta vuelta, a propósito

- **Un negocio es de quien lo cree más quien(es) se unan con el código** —
  no hay límite de personas, pero hoy no hay forma de "sacar" a alguien
  desde la propia app (se haría directo en la tabla `miembros_negocio` de
  Supabase, si hiciera falta).
- **Las sesiones dependen de un token que dura cerca de una hora** — la app
  lo renueva sola en segundo plano; si aun así se vence, simplemente vuelve
  a pedir el correo y la clave.
- **No hay sincronización en vivo mientras los dos miran la app al mismo
  tiempo** — los cambios del otro aparecen al volver a la pestaña o al
  tocar "Actualizar" (se revisa solo cada 30 segundos).
- El contrato, el Excel y todos los cálculos (inversión, mora, categorías de
  gasto) son exactamente los del prototipo original — no se le quitó nada,
  solo se le cambió la piel a un tema claro y se le sumaron cuentas reales.
