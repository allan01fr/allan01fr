@echo off
REM Propostas KAPTEK - dois cliques para abrir a interface no navegador.
cd /d "%~dp0"
if not exist .venv (
  python -c "import sys; sys.exit(sys.version_info < (3, 11))" || (echo Instale o Python 3.11+ em python.org marcando "Add to PATH" & pause & exit /b 1)
  echo Primeira execucao: instalando dependencias, aguarde alguns minutos...
  python -m venv .venv || (echo Instale o Python 3.11+ em python.org marcando "Add to PATH" & pause & exit /b 1)
  call .venv\Scripts\activate
  python -m pip install --upgrade pip
  REM se a instalacao falhar, apaga o .venv para a proxima tentativa reinstalar
  pip install -r requirements.txt || (call deactivate & rmdir /s /q .venv & echo Falha ao instalar as dependencias. Confira a internet e tente de novo. & pause & exit /b 1)
) else (
  call .venv\Scripts\activate
)
REM Evita a pergunta de e-mail do Streamlit na primeira execucao (campo opcional, em branco)
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  mkdir "%USERPROFILE%\.streamlit" 2>nul
  > "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)
streamlit run app\app.py
pause
