# PROTOCOLO DE CAMBIOS — Radicados Semanales

Este documento existe porque en octubre de 2026 se entregó una masiva con 124 radicados de
agosto mezclados y 31 correos rotos, sin que la aplicación dijera una palabra. Ninguno de esos
dos fallos era nuevo: llevaban meses ahí. Lo que faltaba no era más código — era una definición
escrita de **qué significa que la app esté bien**, contra la que cualquier cambio tenga que
chocar antes de salir.

Las pruebas automáticas comprueban lo que quien las escribe **imagina** que puede fallar. Un
fallo que no se le ocurre a nadie no lo prueba nadie. Por eso este protocolo no se apoya en las
pruebas: se apoya en **invariantes sobre el archivo que se entrega** y en **datos reales**.

---

## REGLA 0 — Qué significa "la app está bien"

No es una opinión. Son nueve propiedades que **todo** archivo de masiva entregado debe cumplir.
Se comprueban sobre el .xlsx ya generado, no sobre el código. Cualquiera puede verificarlas, con
la app o sin ella.

| # | Invariante | Cómo se comprueba |
|---|---|---|
| I1 | Ningún radicado repetido | contar únicos vs filas |
| I2 | Todo radicado tiene 15 dígitos y es numérico | expresión regular |
| I3 | Todo radicado del archivo está en el reporte de ORFEO de esa semana | cruce |
| I4 | Ninguna fila con fecha de asignación fuera de la semana declarada | comparar contra el rango |
| I5 | Todo correo tiene estructura válida y dominio conocido | validación real, no "¿tiene arroba?" |
| I6 | Todo comparendo tiene entre 6 y 12 dígitos | longitud |
| I7 | Las dos columnas COMPARENDO coinciden fila por fila | comparación |
| I8 | 27 columnas, con los títulos exactos y en el mismo orden | comparar con la cabecera patrón |
| I9 | Ningún radicado asignado esa semana se queda fuera sin motivo registrado | cruce inverso: ORFEO → archivo, y cada ausencia explicada (agendamiento, devuelto, o salió de la bandeja) |

**Si un cambio rompe una invariante, no sale. Sin excepciones y sin discusión.**

**Cómo se comprueban, en la práctica:** se abre `verificador.html` (está publicado junto a la app,
y también funciona con doble clic sin internet), se sueltan la masiva, el reporte de ORFEO y la
plantilla de agendamientos, y da un veredicto **APTO / NO APTO** con cada caso y su número de fila.
No comparte una sola línea de lógica con la app: si la app se equivoca, el verificador puede
decirlo. Esa independencia es lo que lo hace valer.

`pruebas/caso_2oct/` guarda la masiva, el reporte de ORFEO y los agendamientos de la semana del
2 de octubre de 2026 **anonimizados**, conservando exactamente la forma de cada defecto.
`t23_verificador.py` los pasa por el verificador y exige que encuentre los cinco problemas y que
las otras cuatro invariantes se callen.

Las invariantes se añaden, nunca se quitan. Cada fallo real que aparezca en el trabajo se
convierte en una invariante nueva ese mismo día.

---

## REGLA 1 — La batería completa, verde, antes de cualquier despliegue

```bash
python3 pruebas/mock.py &
python3 pruebas/serve.py pruebas/sitio 8871 &
./pruebas/correr_todo.sh
```

Tiene que decir **TODAS LAS PRUEBAS PASAN**. Una sola falla detiene el despliegue.

`preparar.sh` rehace la copia de pruebas desde el `index.html` real en cada corrida: nunca se
prueba una copia vieja. Esto ya costó días una vez.

---

## REGLA 2 — El caso real manda sobre la prueba imaginada

Cada vez que aparezca un fallo en el trabajo, **antes de arreglarlo**:

1. Se guarda el archivo real que lo demuestra, **anonimizado** (nombres, cédulas y correos
   sustituidos, conservando la forma exacta del defecto).
2. Se escribe una prueba que **falla** con el código actual.
3. Se arregla.
4. La prueba pasa.
5. La prueba se queda para siempre en `pruebas/`.

Una prueba que nunca falló no demuestra nada. Si al escribirla pasa a la primera, está mal
escrita o el fallo era otro.

**Nunca se suben al repositorio datos reales de ciudadanos.** Ya pasó una vez con un
`respaldo.json`; por eso `*.json` y `*.xlsx` están en `.gitignore`.

---

## REGLA 3 — Ningún cambio silencioso en lo que se entrega

Un cambio que altere **qué filas salen** en la masiva o en los agendamientos es la categoría más
peligrosa que existe en esta app. Los dos peores fallos de octubre fueron exactamente eso.

Antes de desplegar un cambio así, es **obligatorio**:

- Correr la masiva **antes** y **después** del cambio sobre los mismos datos.
- Comparar el conjunto de radicados de los dos archivos.
- **Toda diferencia tiene que estar explicada por escrito.** Si aparece o desaparece una fila que
  no se esperaba, el cambio está mal.

Ejemplo real de octubre: al quitar radicados repetidos se juntaron filas sólo por número de
radicado. Un radicado reasignado en otra semana perdía la asignación nueva y salía la vieja. Un
diff antes/después sobre datos reales lo habría enseñado en treinta segundos.

---

## REGLA 4 — Siempre hay vuelta atrás, y se prueba que funciona

- **Netlify guarda todos los despliegues.** En *Deploys* se abre el anterior y se pulsa
  **"Publish deploy"**: la app vuelve a la versión de antes en menos de un minuto. Esto se hace
  sin pedir permiso a nadie en cuanto algo huela mal.
- Antes de cada despliegue se guarda el `.zip` de la versión que está funcionando, con la fecha
  en el nombre.
- Cada despliegue es un commit en la rama, con su mensaje explicando **qué cambia de
  comportamiento**, no qué líneas se tocaron.

Revertir no es un fracaso: es el mecanismo. Lo que no puede pasar es trabajar una semana sobre
una versión rota porque volver atrás daba miedo.

---

## REGLA 5 — Despliegues pequeños, y nunca en viernes ni antes de entregar

- Un cambio por despliegue. Si se juntan cinco cambios y algo sale mal, no se sabe cuál fue.
- **Nunca** se despliega el día de la entrega de la masiva.
- El mejor momento es el lunes temprano: queda la semana entera para notar algo raro.
- Después de desplegar, la primera masiva se revisa con las nueve invariantes **antes** de
  entregarla.

---

## REGLA 6 — El cruce contra ORFEO, siempre, antes de entregar

Es la única verificación que **no depende de que el programa esté bien**. ORFEO es la verdad.

1. ORFEO → reporte *Histórico de radicados asignados a usuario* del rango de la semana.
2. App → Documentos → **¿De dónde sale este número?** → pegar la lista → **Cruzar con mi lista**.
3. Mirar **"Están en ORFEO y NO en tu lista"**. Tiene que ser **0** o tener cada caso explicado
   (agendamiento, devuelto, o ya salió de la bandeja).
4. **Descargar el cruce y guardarlo** en la carpeta de la semana.

Ese archivo guardado, con su fecha, es la prueba documental de qué se asignó y qué se entregó.
Vale ante un memorando aunque el programa tenga fallos.

---

## LAS DOS LISTAS DE CHEQUEO

### Antes de desplegar (quien toca el código)

- [ ] `./pruebas/correr_todo.sh` → TODAS LAS PRUEBAS PASAN
- [ ] Si el cambio toca qué filas salen: diff antes/después sobre datos reales, con cada
      diferencia explicada
- [ ] Las nueve invariantes se cumplen en una masiva generada con la versión nueva
- [ ] La configuración de Supabase está intacta (url y anonKey sin tocar)
- [ ] Guardado el `.zip` de la versión anterior
- [ ] Commit con el mensaje explicando el cambio de comportamiento
- [ ] No es viernes ni día de entrega

### Antes de entregar la masiva (quien hace el trabajo)

- [ ] Reporte de ORFEO de la semana, descargado
- [ ] Cruce hecho en la app: **"En ORFEO y NO en tu lista" = 0** o explicado
- [ ] **"En tu lista y NO en ORFEO" = 0** o explicado (si no, hay arrastre de semanas viejas)
- [ ] Cuadre del conteo: la suma cuadra (aviso verde)
- [ ] Revisión previa: sin hallazgos graves sin confirmar
- [ ] Cruce descargado y guardado en la carpeta de la semana
- [ ] **Semana cerrada** cuando se termina, para que no arrastre a la siguiente

---

## LOS DOS BLOQUES NO SE TOCAN ENTRE SÍ

El trabajo de la mañana (asignaciones de Donina) y el de la tarde (la masiva) tienen
almacenamiento **separado**:

| | Mañana | Tarde (masiva) |
|---|---|---|
| Navegador | `radicados_manana_v1::<correo>` | `radicados_semanales_v2::<correo>` |
| Supabase | columna `manana` | columna `records` |
| Se borra | cada día | cada semana |

`t17_aislamiento.py` toma una foto exacta de todo lo guardado, trabaja a fondo en un bloque y
comprueba que lo del otro **no cambió ni un byte**, en los dos sentidos. `t18_cruces.py` cubre
dos personas en el mismo computador, dos ventanas a la vez y una copia vieja de la nube.

**Verificado el 5 de octubre de 2026:** ninguna función del bloque de la mañana escribe en los
radicados de la masiva. Los 124 radicados de agosto que aparecieron en la masiva **no fueron un
cruce de información**: eran radicados de la masiva, de agosto, que nunca se sacaron de la lista
porque esa semana no se cerró. Acumulación, no contaminación.

Si alguna vez hay que decidir entre los dos bloques, **el de la tarde manda**: es el que produce
lo que se entrega y por lo que se responde.

---

## QUÉ HACER CUANDO ALGO SALE MAL

1. **Revertir primero, investigar después.** Netlify → Deploys → la versión anterior → Publish.
2. **Guardar la evidencia**: el archivo que salió mal, tal cual, sin corregirlo.
3. **Reproducirlo** con datos anonimizados antes de tocar una línea de código.
4. **Escribir la prueba que falla.**
5. Arreglar, prueba verde, batería completa verde, desplegar.
6. **Añadir la invariante nueva a la Regla 0.**

Nunca al revés. Arreglar antes de reproducir es cómo se introducen los dos fallos siguientes.
