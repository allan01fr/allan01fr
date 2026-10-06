@echo off
REM Clima2D - dois cliques para abrir a interface no navegador.
cd /d "%~dp0"
if not exist .venv (
  echo Primeira execucao: instalando dependencias, aguarde alguns minutos...
  python -m venv .venv || (echo Instale o Python 3.11+ em python.org marcando "Add to PATH" & pause & exit /b 1)
  call .venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
streamlit run app\app.py
pause
