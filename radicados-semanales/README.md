# Radicados Semanales

App interna de la Secretaría de Movilidad de Bogotá para clasificar radicados semanales de comparendos y generar el documento final en Excel (formato MASIVA, 27 columnas).

## Qué es

Una sola página (`index.html`), sin backend propio y sin build. Cada persona
se registra con su **correo real de Gmail** y una contraseña, y sus
radicados, ajustes e historial quedan guardados en una base de datos en la
nube (Supabase) — no solo en el caché del navegador. El navegador sigue
guardando una copia local de respaldo (para que la app funcione rápido y no
se trabe si el internet falla un segundo), pero la copia que manda es la de
la nube. No modifica ni reemplaza el Excel oficial de la entidad — es una
herramienta de apoyo para organizar el trabajo y producir el documento
final.

## 1. Crear el proyecto de Supabase

1. Entra a [supabase.com](https://supabase.com) y crea un proyecto nuevo
   (el plan gratis alcanza de sobra). **Importante:** usa un proyecto
   **separado** del que uses para otras apps — este maneja datos de
   personas (nombres, cédulas), así que conviene mantenerlo aparte.
2. **SQL Editor → New query** → pega todo el contenido de
   `supabase/migrations/0001_init.sql` → **Run**.
   (Si el panel de Supabase se rompe con un error raro de `removeChild`,
   ábrelo en una ventana de incógnito e inténtalo de nuevo — es un bug del
   navegador con el panel de Supabase, no de este script.)
3. En **Authentication → Providers → Email**, confirma que el login por
   correo esté activo (viene así por defecto). Si quieres que la gente
   pueda entrar apenas se registre, sin tener que confirmar el correo
   primero, apaga "Confirm email" ahí mismo. Si lo dejas activo, después de
   registrarse van a tener que abrir un correo de confirmación antes de
   poder entrar por primera vez.
4. En **Authentication → URL Configuration**, agrega la URL donde vas a
   publicar la app (la de Netlify, ver abajo) en *Site URL* y en
   *Redirect URLs*.

## 2. Desplegar en Netlify

**Opción rápida — arrastrar y soltar (sin cuenta de GitHub):**
1. Entra a https://app.netlify.com/drop
2. Arrastra la carpeta `radicados-semanales` completa (o solo `index.html`) a la página.
3. Netlify genera un enlace al instante (`https://algo-random.netlify.app`). Puedes renombrarlo desde "Site settings → Change site name".

**Opción recomendada — conectada a este repositorio de GitHub (se actualiza sola con cada cambio):**
1. En Netlify: "Add new site" → "Import an existing project" → conecta con GitHub → elige este repositorio.
2. En "Base directory" pon `radicados-semanales`.
3. Deja "Build command" vacío y "Publish directory" en `.` (ya está indicado en `netlify.toml`).
4. Despliega. Cada vez que se actualice esta carpeta en GitHub, Netlify vuelve a publicar sola.
5. Copia la URL que te dé Netlify y agrégala en Supabase (paso 1.4).

## 3. Conectar la app a tu proyecto de Supabase

1. Abre la URL de Netlify por primera vez.
2. Como todavía no está conectada a ningún proyecto, te va a pedir el
   **Project URL** y la **llave `anon`** — ambos los encuentras en tu
   proyecto de Supabase, en **Project Settings → API**.
3. Pégalos ahí y dale a conectar. Esto solo lo tienes que hacer una vez
   por navegador — la próxima vez ya te pedirá directamente el correo y la
   contraseña.

## 4. Usar la app

1. **Crear cuenta** → tu nombre, tu correo de Gmail y una contraseña
   (mínimo 6 caracteres). Si el proyecto pide confirmar el correo, ábrelo
   y luego entra con tu clave.
2. Desde ahí ya puedes pegar radicados, clasificarlos, y todo se guarda
   automáticamente — verás un aviso de "Guardado" o "Sincronizando…"
   junto a tus datos.
3. **Debes iniciar sesión cada vez que abras la app** (por seguridad, la
   sesión no queda guardada de una visita a otra) — pero tus datos
   siempre están ahí, entres desde el computador que entres.

## Cosas importantes que debes saber

- **Si el servidor de Supabase no responde** (sin internet, proyecto
  pausado, etc.), la app sigue guardando tus cambios en el navegador y
  te avisa con "Guardado local — sin conexión al servidor". En cuanto
  vuelva la conexión, sincroniza sola.
- **Cada persona solo ve sus propios radicados.** La base de datos está
  configurada con seguridad a nivel de fila (RLS), así que ni siquiera
  con el enlace de otro usuario se puede ver su información.
- **Solo se aceptan correos `@gmail.com`** — es una regla explícita del
  proyecto, tanto en la pantalla de registro como en el servidor.
- El Excel oficial de tu Secretaría **nunca se toca ni se modifica** — esta
  app solo genera un archivo nuevo con el formato de la plantilla MASIVA.

## Desarrollo

Es un único archivo HTML/CSS/JS sin build ni dependencias externas (incluye la librería SheetJS embebida para generar archivos `.xlsx` reales, y llama a Supabase directamente por `fetch()`, sin el SDK oficial). Para probarlo localmente basta con abrir `index.html` en el navegador.
