#!/usr/bin/env bash
# Render deck/out/favoured-banks.pptx to one PNG per slide for visual checks.
set -euo pipefail
cd "$(dirname "$0")/out"
rm -rf render && mkdir -p render
soffice --headless --convert-to pdf favoured-banks.pptx --outdir render >/dev/null 2>&1
pdftoppm -r 60 -png render/favoured-banks.pdf render/slide
ls render/slide-*.png | wc -l
