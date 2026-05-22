#!/usr/bin/env bash
set -e

echo "==> Instal·lant dependències Python..."
pip install -r requirements.txt

echo "==> Instal·lant ffmpeg via spotdl..."
python -m spotdl --download-ffmpeg

echo "==> Build complet!"
