# Pruebas de Radicados Semanales

Estas pruebas existen por una razón concreta: **la app la usa a diario un área que responde por
lo que entrega**, y ya hubo una devolución de la jefatura por un dato mal puesto. Cada arreglo
que se hace aquí tiene que quedar comprobado, y los arreglos anteriores tienen que seguir
funcionando después del siguiente.

Viven **en el repositorio a propósito**: el entorno donde se desarrolla se recicla y se lleva por
delante todo lo que no esté commiteado. Ya pasó una vez y hubo que rehacerlas enteras.

## Cómo se corren

Hacen falta `playwright` (con Chromium), `openpyxl` y `node`.

```bash
python3 pruebas/mock.py &                       # hace de Supabase (la de verdad no se toca nunca)
python3 pruebas/serve.py pruebas/sitio 8871 &   # sirve la copia de pruebas
./pruebas/correr_todo.sh
```

`preparar.sh` rehace la copia de pruebas **en cada corrida** a partir del `index.html` de verdad.
No se edita nunca `pruebas/sitio/index_test.html` a mano: es un archivo generado.

## Qué comprueba cada una

| Prueba | Qué defiende |
|---|---|
| `t_rejilla.js`, `t_rejilla2.js` | Que el Excel salga con cuadrícula **sin** estropear las fechas, los acentos ni las 27 columnas. Corre sin navegador. |
| `t1_placa.py` | Que en la columna PLACA salga la placa y no la dirección, venga la tira de Fénix con 14 o con 15 columnas. |
| `t2_tira.py` | Que una tira mal copiada (sin columnas, cortada, corrida) se avise **al momento de pegarla**, y que una fecha de notificación vacía **nunca** se marque como error. |
| `t3_pruebas.py` | La pregunta de SÍ/NO "¿pidió pruebas?" y que la respuesta llegue a la columna FORMATO del archivo entregado. |
| `t4_masiva.py` | Que no se cuelen espacios ni caracteres invisibles en la masiva, y que salga con cuadrícula. |
| `t5_regresion.py` | Que siga intacto lo de antes: las 24 reglas, las imperativas, que DEVUELTO y AGENDAMIENTO no entren en la masiva, y que todas las ventanas abran. |
| `t6_flotante.py` | Que todo lo anterior funcione y **se guarde** igual en la ventana flotante. |
| `t7_imperativas.py` | Que una regla imperativa rota deje el radicado **PENDIENTE** con el aviso fijo, que con eso la masiva **no salga**, y que una fecha ilegible tampoco pase. |
| `t8_concurrencia.py` | Dos ventanas a la vez: en radicados distintos y en el mismo, que ninguna pise a la otra. |
| `t9_flotante_salida.py` | Que la ventana flotante no se quede sin salida cuando el filtro deja la lista vacía. |
| `t10_ruido.py` | Que el aviso **no** salte en radicados sin empezar, y que **sí** salga (caja PENDIENTE) en cuanto uno se trabaja y queda mal; «Guardar y siguiente» no lo deja atrás. |
| `t11_confirmadas.py` | Que una anomalía **no se pueda dar por buena** con un clic (ya no hay «es correcto»), y que con ella la masiva no salga. |
| `t12_cerrar_semana.py` | Que "Cerrar semana" se encuentre sin bucear, pida confirmación, archive todo (incluidos los agendamientos) y no borre nada al cancelar. |
| `t14_memoria_flotante.py` | Que la ventana flotante no pierda lo escrito al cerrarse en seco, que vuelva al radicado donde se quedó, y que cada ventana recuerde lo suyo sin arrastrar a la otra. |
| `t15_manana.py` | El bloque de la mañana, **contra el sheet real de Donina**: que lea las dos hojas, respete los espacios exactos de las clasificaciones, no le añada un punto al radicado, y saque las dos listas con la corrección en negrilla subrayada. |
| `t16_manana_guardado.py` | Que el trabajo de la mañana se guarde en su propia columna, sobreviva a recargar, filtre por tu nombre y se pueda trabajar en la ventana flotante. |
| `t17_aislamiento.py` | Que los dos bloques **no se toquen**: toma una foto exacta de todo lo guardado (navegador y nube), trabaja a fondo en uno, y comprueba que lo del otro no cambió ni un byte. En los dos sentidos. |
| `t18_cruces.py` | Los cruces que faltaban: **dos personas en el mismo computador** (una detrás de otra), **dos ventanas trabajando la mañana a la vez**, y que **una copia vieja de la nube no borre** el día abierto. |
| `t19_sin_clasificar.py` | El caso de la devolución: con un radicado **sin clasificar** la masiva no sale (el botón ya dice «faltan 1» y la app lo abre diciendo qué le falta), y cerrar la semana avisa. |
| `t21_semanas_no_se_mezclan.py` | Que un radicado **reasignado en otra semana** no pierda ninguna de sus dos asignaciones (las dos salen en la plantilla de agendamientos; la masiva no sale con dos semanas y la franja de arriba las nombra), y que un pegado doble de verdad (mismo radicado **y** misma fecha) quede PENDIENTE diciendo que está duplicado. |
| `t22_rango_fechas.py` | La salida por rango se quitó el 04-11-2026: que no se vea, que forzada no entregue nada, que con varias semanas la masiva no salga y nada se descarte solo, y que al quitar el viejo salga. |
| `t20_cuadre_conteo.py` | El caso del número inflado (219 en la app contra 176 aptos en ORFEO): el **mismo radicado repetido** deja sus filas PENDIENTES y la masiva no sale hasta borrar la de sobra; el cuadre **explica** el número, y el cruce contra ORFEO lee radicados con letras y **avisa** si no entendió lo pegado. |
| `t13_opciones.py` | Que las opciones que solo aparecen al hacer algo funcionen: la **doble verificación** de las reglas (con identificador equivocado NO deja), agregar un radicado a mano, la calculadora de término y las cuatro pestañas de Ajustes. |
| `t27_nube_dos_ventanas.py` | La principal y la flotante abiertas a la vez, contra un servidor que se porta como la Supabase **de verdad** (aplica el filtro `actualizado=eq.`). Que ninguna se quede en "conflicto" y deje de subir, que la nube tenga lo de las dos, que un navegador limpio vea todo, y que cerrar la semana justo después de un choque no resucite lo archivado. |
| `t28_estres_cruces.py` | 60 saltos rápidos entre radicados, en las dos ventanas a la vez (escribir y saltar sin esperar, guardar, Tab, esperar). Cada valor lleva dentro el número de su radicado: exige que **ningún radicado tenga datos de otro** y que **no se pierda nada** de lo escrito. Secuencia fija (`SEMILLA=` para probar otra). |
| `t29_lo_absorbido_no_es_mio.py` | El caso que encontró t28, aislado: un correo corregido en la flotante **no puede volver al anterior** cuando la principal guarda otra cosa. |
| `t30_restaurar_punto_no_pisa.py` | Restaurar un punto de restauración devuelve lo borrado **sin deshacer** lo corregido después. |
| `t31_semana_cerrada_no_vuelve.py` | Cerrar la semana con las dos ventanas abiertas, o sin conexión, y volver a entrar: la semana **no vuelve** a la lista y sus radicados siguen en el historial. |
| `t32_solo_radicados.py` | Una lista de **solo números de radicado** entra completa; lo llenado a mano queda en su radicado y sale en la masiva. |
| `t33_sin_fecha_asignacion.py` | Un radicado **sin fecha de asignación** ni nada más se clasifica y se guarda (también desde la flotante) y se ve marcado como «sin fecha»; la masiva **no sale** hasta completarlo; completado, sale; y se cierra con la semana. |
| `t34_lista_como_la_pega.py` | La lista de solo radicados **como llega de verdad** (con comillas y espacios, o copiada de Excel) entra completa; lo que no es un radicado de 15 dígitos queda fuera diciendo por qué (número científico de Excel, dígitos de más o de menos). |
| `t35_comparendo_a_mano.py` | **Todo a mano**, sin línea de Fénix, en la principal y en la flotante: cada casilla sale en su columna de la masiva con el formato de la del 02-10, y corregir una casilla no borra las demás. |
| `t36_tira_en_solo_radicado.py` | Pegar la **tira de Fénix** en un radicado de solo número llena sola las casillas, en la principal y en la flotante. Si trae algo distinto de lo escrito a mano, la app lo muestra en su diálogo y ella elige; corregir una casilla después no borra el documento. |
| `t37_espacio_y_fila_masiva.py` | La casilla **Comentario** ya no está en pantalla, pero un comentario guardado **no se borra**; la flotante cabe en mucho menos alto y muestra la **fila de la masiva** igual, columna por columna, a la del archivo. |
| `t38_flecha_conteo_flotante.py` | En la flotante, el **conteo por formato** y el enlace a informes van ocultos tras una **flecha** que los despliega; en la principal siguen a la vista. |
| `t39_resolucion_mal_escrita.py` | **R29**: una resolución escrita como **fecha** o con **texto pegado** (los dos casos reales de la masiva del 02-10) deja el radicado PENDIENTE con la explicación; las bien escritas no; corregidas, la masiva sale. |
| `t40_inicio_sin_clave.py` | Página de inicio **sin clave** después de la primera vez; la flotante entra sola; y con `mock.py` en modo rotación (como Supabase: cada renovación gasta el token y reusarlo anula la sesión), que las dos ventanas renueven sin anular nada. En la versión del 11-10 la segunda renovación anulaba la sesión y la flotante quedaba «sin conexión al servidor». |
| `t41_pendiente_o_listo.py` | PENDIENTE / LISTO de punta a punta: no avanza mientras falte algo y dice qué, casilla en rojo, «Dejar pendiente y seguir», «Anterior» sí deja volver, dominio de correo que se aprende una vez, ningún «¿es correcto?», y con todo LISTO descarga directo. |
| `t42_flotante_al_dia.py` | La flotante igual de estricta que la principal, las dos al día entre sí **sin mensajes**, y el historial de una semana cerrada en la principal visible en la flotante sin recargar. |

## Reglas de la casa

- **Nunca** se apunta a la Supabase real. `mock.py` es un servidor de mentira que se borra con
  `DELETE /__reset`, y cada prueba arranca de cero.
- Las pruebas manejan la app **por la interfaz** (clics y teclado), no por dentro: así comprueban
  lo mismo que ve la usuaria.
- `mock.py` tiene que portarse **como la Supabase real**, no ser más permisivo. Hasta el 10-10-2026
  aceptaba cualquier escritura, aunque la marca `actualizado` no coincidiera; por eso ninguna prueba
  vio que con dos ventanas abiertas una dejaba de subir a la nube (t27).
- Una prueba que termina siempre con `exit 0` no es una prueba. `t8` y `t9` lo hacían hasta el
  10-10-2026; ahora cuentan sus fallas.
- `t15`–`t18` (bloque de la mañana) se **saltan** si falta `pruebas/sheet_donina.xlsx`, que no se
  sube al repositorio. Una corrida sin ese archivo no las comprobó, aunque diga que todo pasa.
- **Radicados de prueba de 15 dígitos.** Desde el 04-11-2026 un radicado que no tiene 15 dígitos
  queda PENDIENTE (invariante I2), así que los viejos «2026ER200» pasaron a «202670000000200».
- **Un cambio «de otra ventana» se escribe desde otra página** (`ctx.new_page()` en el mismo sitio),
  no desde la misma: escrito desde la misma, la app lo pisa al recargar con lo que tiene en pantalla,
  que es lo correcto.
- Si una prueba falla, primero se mira si la equivocada es la prueba. Ya ha pasado tres veces que
  una "falla" era una prueba mal escrita, y corregir la app por eso habría roto algo que estaba bien.
