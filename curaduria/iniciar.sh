#!/usr/bin/env bash
# Arranca la app. Con --red queda visible para la oficina.
set -euo pipefail
cd "$(dirname "$0")"

direccion="127.0.0.1"
if [[ "${1:-}" == "--red" ]]; then
    direccion="0.0.0.0"
    echo "Modo servidor. Los demás entran a http://$(hostname -I 2>/dev/null | awk '{print $1}'):8501"
fi

exec python3 -m streamlit run app.py --server.address "$direccion"
