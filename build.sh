#!/usr/bin/env bash
set -e

echo "==> Instal·lant dependències Python..."
pip install -r requirements.txt

echo "==> Instal·lant ffmpeg via spotdl..."
echo "y" | python -m spotdl --download-ffmpeg || echo "ffmpeg ja instal·lat o error ignorat"

echo "==> Build complet!"
