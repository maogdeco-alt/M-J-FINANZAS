# Hogar · app definitiva (conectada a Supabase)

`hogar.html` es la app real, con perfiles independientes de verdad (login por correo)
y espacios "Hogar" compartidos por invitación. No es una demo — necesita un proyecto
de Supabase propio para funcionar.

## 1. Crear el proyecto de Supabase

1. Entra a [supabase.com](https://supabase.com), crea una cuenta (gratis) y un proyecto nuevo.
2. Ve a **Authentication → Providers → Email** y confirma que el login por correo (magic
   link) esté activado (viene así por defecto).
3. Ve a **Authentication → URL Configuration** y agrega en *Redirect URLs* la URL exacta
   donde vas a alojar `hogar.html` (ver paso 3). Mientras no la agregues ahí, el enlace
   mágico no te va a dejar entrar.

## 2. Instalar el esquema de base de datos

1. En el proyecto de Supabase, ve a **SQL Editor → New query**.
2. Pega todo el contenido de `supabase/migrations/0001_init.sql` y dale **Run**.
3. Debe correr sin errores. Si algo falla, copia el mensaje de error tal cual para
   que lo revisemos.

## 3. Alojar `hogar.html` en una URL real (https)

El archivo no puede abrirse solo con doble clic para el login — el enlace mágico
necesita redirigir a una URL real. La forma más simple y gratis:

- **GitHub Pages**: en la configuración del repo, activa Pages apuntando a la carpeta
  `app/`. Tu URL quedaría algo como
  `https://maogdeco-alt.github.io/m-j-finanzas/hogar.html`.
- O cualquier hosting estático gratis (Netlify, Vercel, Cloudflare Pages) apuntando a
  este mismo archivo.

Copia esa URL exacta y agrégala en **Authentication → URL Configuration → Redirect
URLs** en Supabase (paso 1.3).

## 4. Conectar la app a tu proyecto

1. Abre la URL de tu `hogar.html` ya publicada.
2. En **Settings (Project Settings → API)** de tu proyecto de Supabase, copia:
   - **Project URL**
   - **anon public key**
3. Pégalas en la pantalla de "Configuración" que te muestra la app la primera vez.
   Quedan guardadas solo en tu navegador — no se suben a ningún lado.

## 5. Usar la app

1. Entra con tu correo → te llega el enlace mágico → lo abres y quedas dentro.
2. Automáticamente tienes tu **espacio personal**.
3. Creas un **Hogar**, le pones nombre, e invitas por correo a quien quieras.
4. Esa persona repite los pasos 1-2 (mismo link de la app, su propio correo) y va a
   ver la invitación esperándola para aceptar.
5. Cualquiera puede **salir de un Hogar** cuando quiera, sin perder su espacio personal
   ni el de los demás Hogares en los que esté.

## Siguientes pasos sugeridos

- Empacar `hogar.html` con [Capacitor](https://capacitorjs.com/) para publicarla en
  App Store / Play Store.
- Sumar categorías, deudas, metas y presupuestos por espacio (mismo patrón de
  `espacio_id` que ya usan `movimientos` y `cuentas`).
- Notificaciones push/correo reales cuando llega una invitación (hoy solo se ve al
  entrar a la app).
