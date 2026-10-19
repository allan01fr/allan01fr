#!/usr/bin/env bash
# Propostas KAPTEK - abre a interface no navegador (Linux/macOS).
cd "$(dirname "$0")"
# .venv/.instalado só existe depois de uma instalação completa; sem ele, reinstala do zero
if [ ! -f .venv/.instalado ]; then
  rm -rf .venv
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' || { echo "Instale o Python 3.11 ou mais novo."; exit 1; }
  # se a instalação falhar, apaga o .venv para a próxima tentativa reinstalar
  python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && touch .venv/.instalado \
    || { rm -rf .venv; echo "Falha ao instalar as dependências. Confira a internet e tente de novo."; exit 1; }
else
  . .venv/bin/activate
fi
# Evita a pergunta de e-mail do Streamlit na primeira execução
if [ ! -f "$HOME/.streamlit/credentials.toml" ]; then
  mkdir -p "$HOME/.streamlit" && printf '[general]\nemail = ""\n' > "$HOME/.streamlit/credentials.toml"
fi
streamlit run app/app.py
