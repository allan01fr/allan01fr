#!/usr/bin/env bash
# Clima2D - abre a interface no navegador (Linux/macOS).
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
else
  . .venv/bin/activate
fi
streamlit run app/app.py
