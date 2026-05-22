#!/usr/bin/env bash
set -e

echo "==> Instal·lant dependències Python..."
pip install -r requirements.txt

echo "==> Instal·lant ffmpeg..."
echo "y" | python -m spotdl --download-ffmpeg || echo "ffmpeg ja instal·lat"

echo "==> Instal·lant Deno..."
echo "y" | python -m spotdl --download-deno || echo "deno ja instal·lat"

echo "==> Build complet!"
