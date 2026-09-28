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

## Reglas de la casa

- **Nunca** se apunta a la Supabase real. `mock.py` es un servidor de mentira que se borra con
  `DELETE /__reset`, y cada prueba arranca de cero.
- Las pruebas manejan la app **por la interfaz** (clics y teclado), no por dentro: así comprueban
  lo mismo que ve la usuaria.
- Si una prueba falla, primero se mira si la equivocada es la prueba. Ya ha pasado tres veces que
  una "falla" era una prueba mal escrita, y corregir la app por eso habría roto algo que estaba bien.
