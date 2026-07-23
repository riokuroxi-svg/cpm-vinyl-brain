#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 2 ]; then
  echo "Uso: ./run_brain.sh imagen.png carpeta_resultado [quick|balanced|quality]"
  exit 1
fi
PROFILE="${3:-quality}"
python3 research/analyzer_v02/run_brain.py \
  --input "$1" \
  --out "$2" \
  --shapes src/main/resources/shapes \
  --profile "$PROFILE" \
  --seed 20260720
