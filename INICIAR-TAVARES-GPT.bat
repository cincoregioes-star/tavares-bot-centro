@echo off
setlocal
chcp 65001 >nul
title TAVARES Bot - GPT Local
cd /d "%~dp0"
echo =====================================================
echo     TAVARES BOT + GPT / CODEX - INICIALIZADOR
echo =====================================================
echo.
set "PYTHON_CMD="
py -3 --version >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  python --version >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [ERRO] Python 3 nao encontrado.
  echo Teste no Prompt de Comando: py --version
  echo https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
echo Python encontrado:
%PYTHON_CMD% --version
where codex >nul 2>nul
if errorlevel 1 (
  echo [ATENCAO] Codex CLI nao encontrado.
  echo Instale Node.js LTS e execute no terminal:
  echo npm install -g @openai/codex
  echo Depois: codex login
  echo.
  echo O servidor podera iniciar, mas o GPT so funcionara apos instalacao e login.
)
echo Iniciando servidor local em 127.0.0.1:8765...
%PYTHON_CMD% "desktop\tavares_bridge.py"
if errorlevel 1 (
  echo.
  echo O programa terminou com erro. Confira as mensagens acima.
  pause
)
endlocal
