@echo off
setlocal
chcp 65001 >nul
title TAVARES Bot - GPT Local
cd /d "%~dp0"
echo =====================================================
echo     TAVARES BOT + GPT / CODEX - INICIALIZADOR
echo =====================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python 3 nao encontrado.
  echo Instale Python 3 e marque Add Python to PATH.
  echo https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
where codex >nul 2>nul
if errorlevel 1 (
  echo [ATENCAO] Codex CLI nao encontrado.
  echo Instale Node.js LTS e execute no terminal:
  echo npm install -g @openai/codex
  echo Em seguida: codex login
  echo.
  echo O servidor podera iniciar, mas o GPT so funcionara apos instalacao e login.
)
echo Iniciando servidor local em 127.0.0.1:8765...
python "desktop\tavares_bridge.py"
if errorlevel 1 (
  echo.
  echo O programa terminou com erro. Confira as mensagens acima.
  pause
)
endlocal
