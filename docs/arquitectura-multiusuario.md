# Arquitectura multiusuario — de "cuenta de hogar" a usuarios independientes con espacios compartidos

Este documento nace de una revisión del prototipo funcional adjunto (`index_10.html`, app
de una sola página "J&M · Cuentas") y propone cómo evolucionar su modelo de datos para
escalarlo a una app de celular donde **cada persona se registra y se loguea por su cuenta**,
y luego puede **invitar a otras personas ya registradas a crear cuentas en común**, pudiendo
tener varios espacios compartidos con distintas personas al mismo tiempo.

## 1. Diagnóstico del prototipo actual

El prototipo ya usa **Supabase** como backend, aunque no es evidente a simple vista:

- `enviarEnlace(correo)` → `POST /auth/v1/otp` — login real por magic link, **por persona**.
- `capturarSesion()` — captura `access_token`/`refresh_token` del hash de la URL (flujo implícito de Supabase Auth).
- `traerHogar()` → `GET /rest/v1/hogares?select=...&limit=1` (PostgREST).
- `subirHogar()` → `PATCH /rest/v1/hogares?id=eq.<id>` con `{estado: D}` — sube **todo el estado de la app** de una vez, con debounce de 1.5s.
- `unirseHogar(codigo)` → `POST /rest/v1/miembros {hogar: codigo}` — el "código para que la otra persona entre" es el **UUID de la fila `hogares`**, copiado y pegado a mano. No hay tabla de invitaciones.

Es decir: **el login ya es individual y real** (correo propio, sesión propia). Lo que no es
individual es el **modelo de datos**:

- Cada usuario autenticado se ata a **una sola fila `hogares`** (`limit=1`): no puede
  pertenecer a más de un espacio compartido a la vez.
- Dentro de esa fila, todo el estado vive en **un blob JSON** (`estado`): `personas:{a,b}`,
  `pins:{a,b}`, `cuentas`, `movs`, `deudas`, `metas`, etc. — sin importar cuántos usuarios
  reales estén autenticados contra ese hogar.
- "A" y "B" no son usuarios del sistema: son **dos casilleros fijos** dentro del blob,
  separados por un PIN de 4 dígitos guardado en el dispositivo. El propio texto de la UI lo
  admite: *"Separa los bloques, no es una caja fuerte"*.
- Compartir acceso = pegar un UUID. No hay invitación real (sin destinatario, sin
  aceptar/rechazar, sin expiración).
- El reparto (`D.reparto.a/b`) asume exactamente dos personas, hardcodeadas.

Esto explica la limitación exacta que se quiere resolver: hoy el diseño es
**"hogar-primero"** (un contenedor compartido con casilleros internos); se quiere pasar a
**"usuario-primero"** (una identidad con su propio espacio, que además puede pertenecer a
varios espacios compartidos).

## 2. Modelo propuesto

### Entidades

| Entidad | Reemplaza a | Descripción |
|---|---|---|
| `usuarios` | (implícito en `auth.users`) | Espejo 1:1 de `auth.users` de Supabase. Nombre visible, correo, avatar. |
| `espacios` | `hogares` | Un espacio financiero: `tipo` = `personal` \| `compartido`. Cada usuario tiene **un** espacio personal, creado automáticamente al registrarse, intransferible. Un espacio compartido nace al aceptarse una invitación. |
| `miembros_espacio` | `miembros` + `personas`/`pins` | Tabla puente `usuario_id` ↔ `espacio_id`, con `rol` (`propietario`\|`miembro`), `reparto_pct`, `estado` (`activo`\|`salio`), `fecha_union`. Un usuario puede tener **N filas**, una por cada espacio compartido en el que participa. |
| `invitaciones` | el "pegar el UUID" | `espacio_id` (o null si se crea junto con la invitación), `de_usuario_id`, `para_correo`/`para_usuario_id`, `token`, `estado` (`pendiente`\|`aceptada`\|`rechazada`\|`expirada`), `reparto_propuesto`, `creado_en`, `expira_en`. |
| `cuentas` | `D.cuentas[].bloque` | Cuentas bancarias/billeteras, ahora con `espacio_id` en vez de `bloque:'a'|'b'|'casa'`. |
| `movimientos`, `fijos`, `deudas`, `metas`, `activos`, `notas`, `proyectos` | ídem, dentro del blob `estado` | Cada tabla pasa a tener `espacio_id` y, cuando aplica, `usuario_id` (quién registró/pagó) en vez de `de:'a'|'b'`. |

### Relación usuario ↔ espacios

```
usuario "Mao"
 ├── espacio personal "Mao" (tipo=personal, único, automático)
 ├── espacio compartido "Casa" (con Juan)         ← vía miembros_espacio
 ├── espacio compartido "Finanzas con mamá"        ← vía miembros_espacio
 └── espacio compartido "Viaje Cartagena" (con 3)  ← vía miembros_espacio
```

Esto es lo que hoy es **imposible**: el `limit=1` en `traerHogar()` asume un solo hogar por
usuario. Con `miembros_espacio` como tabla N:M, un usuario puede estar en cualquier número
de espacios compartidos, cada uno con personas distintas y su propio reparto.

### Seguridad: RLS en vez de PIN local

Hoy el PIN separa casilleros *dentro del mismo dispositivo*, pero cualquiera con el UUID del
hogar puede unirse y ver todo. Con el modelo normalizado, cada tabla (`cuentas`,
`movimientos`, etc.) lleva `espacio_id`, y una política RLS del estilo:

```sql
using (
  espacio_id in (
    select espacio_id from miembros_espacio
    where usuario_id = auth.uid() and estado = 'activo'
  )
)
```

hace cumplir el acceso **en la base de datos**, no en la UI. Eso sí es una caja fuerte real
— y de paso resuelve el matiz que ya reconocía el propio prototipo.

## 3. Flujos clave

**Registro / login** (esto casi no cambia — ya es correcto):
usuario entra su correo → magic link de Supabase Auth → sesión propia. Al primer login se
crea automáticamente su `espacio personal`.

**Invitar a alguien a un espacio en común**:
1. Usuario A, desde su portal, elige "Invitar a alguien" → busca por correo (usuario ya
   registrado o no) → opcionalmente propone nombre del espacio ("Casa") y reparto (50/50).
2. Se crea una fila en `invitaciones` con `token` y `expira_en`.
3. Usuario B ve la invitación en una bandeja (in-app + notificación/correo) → acepta o
   rechaza.
4. Al aceptar: se crea (o reutiliza) el `espacio compartido`, se inserta a A y B en
   `miembros_espacio`. El espacio aparece en el selector de ambos.
5. Se puede repetir: A puede tener otro espacio compartido con C, sin que eso afecte el
   espacio que tiene con B.

**Selector de espacios** (reemplaza el portal fijo "Casa / Persona A / Persona B"):
lista dinámica generada desde `miembros_espacio` del usuario logueado — su espacio personal
siempre primero, luego cada espacio compartido con el nombre que le dieron y con quién lo
comparte.

**Salir de un espacio compartido**: el miembro cambia su fila a `estado='salio'`; pierde
acceso a nuevas lecturas/escrituras (por RLS), pero se decide aparte si el histórico de
movimientos que generó se conserva (recomendado: conservarlo, mostrando su nombre, igual que
hoy se conserva un movimiento aunque cambie el reparto).

## 4. Migración desde el prototipo

- `bloque:'casa'` → el espacio compartido existente de ese hogar.
- `bloque:'a'` / `bloque:'b'` → espacio personal del usuario correspondiente.
- `D.personas.a/b` → nombres visibles de los dos usuarios ya reales (Supabase Auth) que hoy
  están detrás de ese hogar.
- El UUID de `hogares` que hoy se comparte manualmente puede mapearse 1:1 al `espacio_id`
  del nuevo `espacio compartido`, para no perder el histórico de quienes ya lo usan.
- Se necesita un script de import único que lea el blob `estado` de cada `hogares` y lo
  explote en filas de las tablas nuevas.

## 5. Ruta recomendada a app de celular

El prototipo es HTML/CSS/JS **sin framework**, con render manual a strings — no hay nada que
"portar" de UI en el sentido de React/Vue. Dado que ya habla con Supabase vía REST, la ruta
de menor fricción es:

1. Mantener la UI actual (o evolucionarla) y empacar con **Capacitor** para publicar a
   iOS/Android reutilizando prácticamente todo el JS existente, en vez de reescribir en
   React Native/Flutter desde cero.
2. El trabajo grande no es de UI sino de **datos**: pasar de `save(D)`/`load(cb)` con un
   blob único a llamadas normalizadas contra las tablas nuevas (Supabase ya trae
   Realtime, útil para que los cambios de un espacio compartido aparezcan en vivo en el
   otro dispositivo, sin el polling actual de `setInterval(...,20000)`).
3. Notificaciones push (para invitaciones y avisos de pago) vía Supabase + un servicio como
   FCM/APNs, integrable después de tener la app empacada con Capacitor.

## 6. Preguntas abiertas para definir el siguiente paso

1. **Invitación**: ¿por correo (como ya usa `enviarEnlace`), por buscar nombre de usuario, o
   por link/código compartible? ¿O varias opciones a la vez?
2. **Tamaño de espacio compartido**: ¿solo parejas (2 personas) o también espacios con 3+
   miembros (familia, roommates, viaje)?
3. **Reparto**: ¿se define al crear la invitación o se puede ajustar después entre los
   miembros?
4. **Datos históricos**: si alguien sale de un espacio compartido, ¿su histórico de
   movimientos se queda visible para los demás miembros?
5. **Prioridad de plataforma**: ¿iOS, Android o ambas desde el inicio?
6. **Confirmación de stack**: ¿seguimos con Supabase (ya hay indicios claros en el código:
   Auth por magic link + PostgREST) o se evalúa otra opción?

Con respuestas a esto se puede pasar a definir el esquema SQL exacto (con políticas RLS) y
el plan de implementación por fases.
