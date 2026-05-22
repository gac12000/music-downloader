#!/usr/bin/env bash
set -e

echo "==> Instal·lant dependències Python..."
pip install -r requirements.txt

echo "==> Instal·lant ffmpeg..."
apt-get update -qq && apt-get install -y -qq ffmpeg

echo "==> Build complet!"
