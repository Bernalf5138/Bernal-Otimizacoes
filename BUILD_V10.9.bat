@echo off
REM ==========================================================================
REM  Bernal Otimizacoes Pro - Builder do Setup V10.9  (rode no Windows)
REM  Gera:  dist\Setup_Bernal_Otimizacoes_V10.9.exe
REM ==========================================================================
setlocal
cd /d "%~dp0"
chcp 65001 >nul
title Build Bernal Otimizacoes V10.9

echo.
echo ========================================================
echo   BERNAL OTIMIZACOES PRO - BUILD DO SETUP V10.9
echo ========================================================
echo.

REM Fecha o app se estiver aberto (senao o PyInstaller nao regrava o .exe)
taskkill /F /IM BernalOtimizacoes.exe >nul 2>&1

where py >nul 2>&1 && (set "PY=py") || (set "PY=python")
%PY% --version >nul 2>&1 || (echo [ERRO] Python nao encontrado no PATH. Instale o Python 3 e marque "Add to PATH". & pause & exit /b 1)

echo [1/4] Conferindo/instalando dependencias...
%PY% -m pip install --upgrade pyinstaller customtkinter psutil pillow cryptography || (echo [ERRO] Falha ao instalar dependencias. & pause & exit /b 1)

echo.
echo [2/4] Verificando o codigo (sintaxe)...
%PY% -m py_compile OtimizadorGamer.py idiomas.py installer.py || (echo [ERRO] O codigo tem erro de sintaxe. & pause & exit /b 1)

echo.
echo [3/4] Compilando o aplicativo principal (BernalOtimizacoes.exe)...
%PY% -m PyInstaller --noconfirm --clean BernalOtimizacoes.spec || (echo [ERRO] Falha ao compilar o app principal. & pause & exit /b 1)
if not exist "dist\BernalOtimizacoes.exe" (echo [ERRO] dist\BernalOtimizacoes.exe nao foi gerado. & pause & exit /b 1)

echo.
echo [4/4] Compilando o instalador (Setup_Bernal_Otimizacoes_V10.9.exe)...
%PY% -m PyInstaller --noconfirm --clean "Setup_Bernal_Otimizacoes_V10.9.spec" || (echo [ERRO] Falha ao compilar o instalador. & pause & exit /b 1)

echo.
if exist "dist\Setup_Bernal_Otimizacoes_V10.9.exe" (
    echo ========================================================
    echo   PRONTO!  Seu instalador esta em:
    echo   %CD%\dist\Setup_Bernal_Otimizacoes_V10.9.exe
    echo ========================================================
    explorer /select,"%CD%\dist\Setup_Bernal_Otimizacoes_V10.9.exe"
) else (
    echo [ERRO] O instalador nao foi gerado. Leia as mensagens acima.
)
echo.
pause
endlocal
