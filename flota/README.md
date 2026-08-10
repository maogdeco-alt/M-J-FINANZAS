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
   **llave pública (anon)** — están en Supabase, en **Project Settings →
   API**. Se guardan en este navegador; no hay que repetirlo cada vez.

## 4. Usar la app

1. **Crear cuenta** → tu nombre, tu correo, tu contraseña (mínimo 6
   caracteres). Si el proyecto pide confirmar el correo, ábrelo y luego
   entra con tu clave.
2. La primera persona que entra ve dos opciones: **➕ Crear un negocio** (le
   pone nombre y genera un código de 6 letras) o **🔑 Unirme con un
   código** (si su pareja ya lo creó y le compartió el código).
3. Comparte el código por el medio que sea (WhatsApp, de palabra) — sirve
   una sola vez. Si se pierde, se puede generar uno nuevo desde
   **⚙️ Ajustes → Tu negocio**.
4. Ya adentro, los dos ven y editan la misma información: motos,
   conductores, pagos, gastos, cuentas y contratos.

## Cómo está pensada la seguridad

- Cada quien tiene su propia cuenta (correo + contraseña) — no hay una sola
  clave compartida como en el borrador inicial.
- La base de datos usa RLS (seguridad por fila): solo quienes pertenecen al
  negocio pueden leer o escribir sus datos — se hace cumplir en la base de
  datos, no solo en la pantalla.
- Cada pago, gasto, moto y conductor que se registra queda con el nombre de
  quién lo registró (se ve en la lista, y también en el Excel exportado).

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
