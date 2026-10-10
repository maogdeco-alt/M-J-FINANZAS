#!/bin/bash
# Corre TODAS las pruebas contra el index.html de verdad, recién copiado.
#
#   1. python3 pruebas/mock.py        (en otra terminal: hace de Supabase)
#   2. python3 pruebas/serve.py pruebas/sitio 8871   (en otra: sirve la copia de pruebas)
#   3. ./pruebas/correr_todo.sh
P="$(cd "$(dirname "$0")" && pwd)"
# UN CANDADO. Dos corridas a la vez comparten el servidor de mentira y la copia de pruebas, y se
# pisan: salen "fallas" que no son de la app sino del choque. Pasó una vez y costó rato entenderlo.
LOCK="$P/.corriendo"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "Ya hay otra corrida en marcha (si no es cierto, borra $LOCK)."; exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
"$P/preparar.sh" || exit 1
cd "$P"
mal=0
echo ""
echo "############ el Excel con cuadrícula (sin navegador)"
node t_rejilla.js  || mal=$((mal+1))
node t_rejilla2.js || mal=$((mal+1))
for t in t1_placa.py t2_tira.py t3_pruebas.py t4_masiva.py t5_regresion.py t6_flotante.py t7_imperativas.py t8_concurrencia.py t9_flotante_salida.py t10_ruido.py t11_confirmadas.py t12_cerrar_semana.py t13_opciones.py t14_memoria_flotante.py t15_manana.py t16_manana_guardado.py t17_aislamiento.py t18_cruces.py t19_sin_clasificar.py t20_cuadre_conteo.py t21_semanas_no_se_mezclan.py t22_rango_fechas.py t23_verificador.py t24_reglas_correo_radicado_comparendo.py t25_masiva_mezcla_semanas.py t26_manana_apagado.py; do
  echo ""
  echo "############ $t"
  python3 "$t" || mal=$((mal+1))
done
echo ""
echo "################################"
if [ "$mal" -eq 0 ]; then echo "TODAS LAS PRUEBAS PASAN"; else echo "$mal PRUEBA(S) CON FALLAS"; fi
exit $mal
