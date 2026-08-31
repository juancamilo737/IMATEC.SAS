#!/bin/bash
# ============================================================
#  IMATEC S.A.S. — Arrancar el sistema
#  Doble clic en este archivo (o ejecutarlo en la Terminal).
# ============================================================
cd "$(dirname "$0")" || exit 1

if [ ! -d ".venv" ]; then
  echo "Instalando por primera vez… (esto tarda un par de minutos)"
  python3 -m venv .venv || { echo "No se encontró Python 3. Instálelo desde python.org"; exit 1; }
  ./.venv/bin/python -m pip install --quiet --upgrade pip
  ./.venv/bin/python -m pip install --quiet -r requirements.txt
fi

echo ""
echo "  IMATEC S.A.S. — sistema en marcha"
echo "  ---------------------------------------------"
echo "  Sitio web ........ http://localhost:8000"
echo "  Panel de gestión . http://localhost:8000/admin"
echo "  Portal cliente ... http://localhost:8000/portal"
echo ""
echo "  Para apagarlo: presione Control + C"
echo ""

sleep 1 && open http://localhost:8000 2>/dev/null &
exec ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
