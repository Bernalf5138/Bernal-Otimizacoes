@echo off
REM Publica a release V10.9 no GitHub (usa o login git ja salvo na sua maquina).
REM Rode DEPOIS do BUILD_V10.9.bat ter gerado os .exe na pasta dist.
cd /d "%~dp0"
chcp 65001 >nul
title Publicar Release V10.9 no GitHub
where py >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% create_release.py
pause
