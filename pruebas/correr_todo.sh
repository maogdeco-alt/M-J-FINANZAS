#!/bin/bash
# Corre TODAS las pruebas contra el index.html de verdad, recién copiado.
#
#   1. python3 pruebas/mock.py        (en otra terminal: hace de Supabase)
#   2. python3 pruebas/serve.py pruebas/sitio 8871   (en otra: sirve la copia de pruebas)
#   3. ./pruebas/correr_todo.sh
P="$(cd "$(dirname "$0")" && pwd)"
"$P/preparar.sh" || exit 1
cd "$P"
mal=0
echo ""
echo "############ el Excel con cuadrícula (sin navegador)"
node t_rejilla.js  || mal=$((mal+1))
node t_rejilla2.js || mal=$((mal+1))
for t in t1_placa.py t2_tira.py t3_pruebas.py t4_masiva.py t5_regresion.py t6_flotante.py; do
  echo ""
  echo "############ $t"
  python3 "$t" || mal=$((mal+1))
done
echo ""
echo "################################"
if [ "$mal" -eq 0 ]; then echo "TODAS LAS PRUEBAS PASAN"; else echo "$mal PRUEBA(S) CON FALLAS"; fi
exit $mal
