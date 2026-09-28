#!/bin/bash
# Rehace SIEMPRE la copia de pruebas a partir del index.html de verdad, y saca de él los dos
# trozos de JavaScript que se prueban sueltos (la librería de Excel y el generador de cuadrícula).
#
# Existe porque una vez se estuvo auditando durante días una copia de hacía cinco días sin
# darse cuenta: si la copia no se rehace en cada corrida, las pruebas mienten.
set -e
P="$(cd "$(dirname "$0")" && pwd)"
APP="$P/../radicados-semanales/index.html"
mkdir -p "$P/sitio"
# La app apunta a la Supabase de verdad; la copia de pruebas apunta al servidor de mentira.
sed 's#https://hgfqoodogpxhqbdyubsd.supabase.co#http://127.0.0.1:9870#g' "$APP" > "$P/sitio/index_test.html"
grep -q '127.0.0.1:9870' "$P/sitio/index_test.html"
cp "$P/../radicados-semanales/sw.js" "$P/../radicados-semanales/manifest.webmanifest" "$P/sitio/" 2>/dev/null || true
cp -r "$P/../radicados-semanales/icons" "$P/sitio/" 2>/dev/null || true
python3 - "$APP" "$P" <<'PY'
import re, sys
app_path, dest = sys.argv[1], sys.argv[2]
s = open(app_path, encoding="utf-8").read()
bloques = re.findall(r'<script\b[^>]*>([\s\S]*?)</script>', s)
libreria = max(bloques, key=len) if False else None
# la librería de Excel viene minificada en una sola línea gigante; la app son miles de líneas
lib = [b for b in bloques if len(b) > 100000 and b.count("\n") < 50]
codigo = [b for b in bloques if b.count("\n") > 500]
assert len(lib) == 1 and len(codigo) == 1, (len(lib), len(codigo))
open(dest + "/sheetjs.js", "w", encoding="utf-8").write(lib[0])
c = codigo[0]
ini = c.index("  var CRC_TABLA = (function(){")
fin = c.index("  // Descarga un .xlsx real (formato binario de Excel")
open(dest + "/rejilla.js", "w", encoding="utf-8").write(c[ini:fin])
print("copia de pruebas rehecha:", s.count(chr(10)) + 1, "líneas")
PY
