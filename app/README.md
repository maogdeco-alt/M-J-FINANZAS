# La app real — cuentas individuales (correo + contraseña) + Casa por código

`original.html` ahora es la app completa (todo lo que ya conoces: deudas, metas,
Chanchi, análisis...) conectada a cuentas 100% individuales. Cada quien se
registra con su correo y su contraseña. Desde su cuenta, puede crear una
**Casa** (genera un código corto) o unirse a una con el código que le
compartieron.

## 1. Crear el proyecto de Supabase

1. Entra a [supabase.com](https://supabase.com), crea un proyecto (gratis).
2. **SQL Editor → New query** → pega todo el contenido de
   `supabase/migrations/0002_cuentas_individuales.sql` → **Run**.
   (Si te sale la advertencia de "operaciones destructivas", es normal —
   dale a confirmar. Si el panel se rompe con un error de `removeChild`,
   ábrelo en una ventana de incógnito e inténtalo de nuevo — es un bug del
   navegador con el panel de Supabase, no de este script.)
3. En **Authentication → Providers → Email**, confirma que el login por
   correo esté activo (viene así por defecto). Si quieres que la gente
   pueda entrar apenas se registre, sin confirmar el correo primero, puedes
   apagar "Confirm email" ahí mismo — si lo dejas activo, después de
   registrarse van a tener que abrir un correo de confirmación antes de
   poder entrar.
4. En **Authentication → URL Configuration**, agrega la URL donde vas a
   publicar la app (ver paso 3 más abajo) en *Site URL* y en *Redirect URLs*.

## 2. Publicar `original.html` en Netlify

Igual que ya sabes hacerlo:

1. Descarga `app/original.html`.
2. Ponlo en una carpeta y **cámbiale el nombre a `index.html`**.
3. Arrastra la carpeta a Netlify.
4. Copia la URL que te da Netlify y agrégala en Supabase (paso 1.4).

## 3. Conectar la app a tu proyecto

1. Abre la URL de Netlify.
2. Pega tu **Project URL** y tu **llave anon** (Supabase → Project Settings
   → API) en la pantalla de "Conectar".

## 4. Usar la app

1. **Crear cuenta** → tu nombre, tu correo, tu contraseña (mínimo 6
   caracteres). Si el proyecto pide confirmar el correo, ábrelo y luego
   entra con tu clave.
2. Ya adentro, en el portal ves **"Tu espacio personal"** — solo tuyo.
3. Si tenías datos de prueba cargados en este navegador de sesiones
   anteriores, la primera vez que entres se copian automáticamente a tu
   espacio personal nuevo.
4. **"+ Crear una Casa"** → le pones nombre → te da un código corto →
   se lo compartes a tu pareja o familiar (por WhatsApp, de palabra, como
   sea).
5. La otra persona crea su propia cuenta (paso 1 de este punto), y en el
   portal le da a **"Unirme con un código"** → pega el código → ya están
   los dos adentro de la misma Casa.
6. Dentro de un gasto personal, si marcas "Es de la Casa", queda anotado
   directamente en la Casa (no en tu espacio), atribuido a ti — así
   funciona el cruce de cuentas.

## Lo que queda por fuera de esta vuelta, a propósito

- **Por ahora una Casa es de máximo 2 personas.** Abrirla a 3+ (para
  familias, roommates) es la siguiente fase — el motor de reparto y
  aportes hoy está construido para exactamente dos.
- **Si tienes más de una Casa**, "¿es de la Casa?" usa la primera de la
  lista — elegir cuál queda pendiente.
- **Las sesiones duran alrededor de una hora.** Si llevas mucho rato con la
  pestaña abierta sin recargar, puede que tengas que volver a entrar.
- **Se quitó el resumen semanal por correo** (estaba pensado para el modelo
  anterior de un solo hogar; se puede rehacer más adelante apuntado a cada
  espacio).
- No hay sincronización en vivo mientras los dos están viendo la Casa al
  mismo tiempo — los cambios se ven al volver a entrar al espacio.
