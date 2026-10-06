#!/usr/bin/env bash
# Clima2D - abre a interface no navegador (Linux/macOS).
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
else
  . .venv/bin/activate
fi
# Evita a pergunta de e-mail do Streamlit na primeira execução
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
  mkdir -p "$HOME/.streamlit" && printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
fi
streamlit run app/app.py
