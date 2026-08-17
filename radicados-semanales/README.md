# Radicados Semanales

App interna de la Secretaría de Movilidad de Bogotá para clasificar radicados semanales de comparendos y generar el documento final en Excel (formato MASIVA, 27 columnas).

## Qué es

Una sola página (`index.html`), sin backend, sin base de datos externa. Todo el trabajo se guarda en el navegador de quien la usa (localStorage), separado por cuenta (cada persona inicia sesión con su correo de Gmail). No modifica ni reemplaza el Excel oficial de la entidad — es una herramienta de apoyo para organizar el trabajo y producir el documento final.

## Desplegar en Netlify

**Opción rápida — arrastrar y soltar (sin cuenta de GitHub):**
1. Entra a https://app.netlify.com/drop
2. Arrastra la carpeta `radicados-semanales` completa (o solo `index.html`) a la página.
3. Netlify genera un enlace al instante (`https://algo-random.netlify.app`). Puedes renombrarlo desde "Site settings → Change site name".

**Opción recomendada — conectada a este repositorio de GitHub (se actualiza sola con cada cambio):**
1. En Netlify: "Add new site" → "Import an existing project" → conecta con GitHub → elige este repositorio.
2. En "Base directory" pon `radicados-semanales`.
3. Deja "Build command" vacío y "Publish directory" en `.` (ya está indicado en `netlify.toml`).
4. Despliega. Cada vez que se actualice esta carpeta en GitHub, Netlify vuelve a publicar sola.

## Desarrollo

Es un único archivo HTML/CSS/JS sin build ni dependencias externas (incluye la librería SheetJS embebida para generar archivos `.xlsx` reales). Para probarlo localmente basta con abrir `index.html` en el navegador.
