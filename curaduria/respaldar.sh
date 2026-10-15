#!/usr/bin/env bash
# Copia la biblioteca de bloques y las plantillas a una carpeta con fecha.
set -euo pipefail
cd "$(dirname "$0")"

destino="respaldos/$(date +%Y-%m-%d)"
mkdir -p "$destino"
cp -r biblioteca "$destino/" 2>/dev/null || true
cp -r plantillas "$destino/" 2>/dev/null || true
echo "Respaldo en $destino"
