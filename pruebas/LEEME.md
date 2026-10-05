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
| `t7_imperativas.py` | Que las reglas imperativas se vuelvan a mirar **al entregar**, que el aviso quede fijo en pantalla, y que una fecha ilegible no salga en blanco sin avisar. |
| `t8_concurrencia.py` | Dos ventanas a la vez: en radicados distintos y en el mismo, que ninguna pise a la otra. |
| `t9_flotante_salida.py` | Que la ventana flotante no se quede sin salida cuando el filtro deja la lista vacía. |
| `t10_ruido.py` | Que el aviso **no** salte en radicados sin empezar, y que **sí** salte en cuanto uno se trabaja y queda mal. |
| `t11_confirmadas.py` | Que las anomalías confirmadas durante la semana se vean antes de entregar la base. |
| `t12_cerrar_semana.py` | Que "Cerrar semana" se encuentre sin bucear, pida confirmación, archive todo (incluidos los agendamientos) y no borre nada al cancelar. |
| `t14_memoria_flotante.py` | Que la ventana flotante no pierda lo escrito al cerrarse en seco, que vuelva al radicado donde se quedó, y que cada ventana recuerde lo suyo sin arrastrar a la otra. |
| `t15_manana.py` | El bloque de la mañana, **contra el sheet real de Donina**: que lea las dos hojas, respete los espacios exactos de las clasificaciones, no le añada un punto al radicado, y saque las dos listas con la corrección en negrilla subrayada. |
| `t16_manana_guardado.py` | Que el trabajo de la mañana se guarde en su propia columna, sobreviva a recargar, filtre por tu nombre y se pueda trabajar en la ventana flotante. |
| `t17_aislamiento.py` | Que los dos bloques **no se toquen**: toma una foto exacta de todo lo guardado (navegador y nube), trabaja a fondo en uno, y comprueba que lo del otro no cambió ni un byte. En los dos sentidos. |
| `t18_cruces.py` | Los cruces que faltaban: **dos personas en el mismo computador** (una detrás de otra), **dos ventanas trabajando la mañana a la vez**, y que **una copia vieja de la nube no borre** el día abierto. |
| `t19_sin_clasificar.py` | El caso de la devolución: que un radicado **sin clasificar** no pueda quedarse fuera de la masiva en silencio, ni archivarse al cerrar la semana sin avisar. |
| `t21_semanas_no_se_mezclan.py` | Que un radicado **reasignado en otra semana** no pierda ninguna de sus dos asignaciones: las dos salen en la masiva y en la plantilla de agendamientos, y la app avisa en vez de decidir cuál vale. Y que un pegado doble de verdad (mismo radicado **y** misma fecha de asignación) sí se junte en una sola fila. |
| `t22_rango_fechas.py` | Que se pueda sacar **solo un rango de fechas de asignación** ("desde el 28 de septiembre hasta ahora"): que lo anterior al rango no se cuele, que de cada radicado salga **una sola fila** (la asignación más reciente del rango), que lo que no tenga fecha legible se liste en vez de desaparecer, y que el botón normal de la masiva siga sacando **todo** sin recortar nada. |
| `t20_cuadre_conteo.py` | El caso del número inflado (219 en la app contra 176 aptos en ORFEO): que el **mismo radicado repetido** no salga dos veces en el archivo ni infle el contador, que el cuadre **explique** el número y la suma cuadre, y que el cruce contra ORFEO lea radicados con letras y **avise** si no entendió lo pegado en vez de declarar que todo sobra. |
| `t13_opciones.py` | Que las opciones que solo aparecen al hacer algo funcionen: la **doble verificación** de las reglas (con identificador equivocado NO deja), agregar un radicado a mano, la calculadora de término y las cuatro pestañas de Ajustes. |

## Reglas de la casa

- **Nunca** se apunta a la Supabase real. `mock.py` es un servidor de mentira que se borra con
  `DELETE /__reset`, y cada prueba arranca de cero.
- Las pruebas manejan la app **por la interfaz** (clics y teclado), no por dentro: así comprueban
  lo mismo que ve la usuaria.
- Si una prueba falla, primero se mira si la equivocada es la prueba. Ya ha pasado tres veces que
  una "falla" era una prueba mal escrita, y corregir la app por eso habría roto algo que estaba bien.
