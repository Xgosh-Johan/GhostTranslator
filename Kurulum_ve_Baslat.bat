@echo off
chcp 65001 >nul
title Ghost Translator - Kurulum ve Baslatici
color 0A

cd /d "%~dp0"

echo ====================================================================
echo     GHOST TRANSLATOR - OTOMATIK KURULUM VE BASLATICI
echo ====================================================================
echo.

:: Python komutunu tespit et
set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py"
if not defined PY_CMD (
    where python >nul 2>&1 && set "PY_CMD=python"
)

if not defined PY_CMD (
    color 0C
    echo [HATA] Bilgisayarinizda Python kurulu bulunamadi!
    echo Lutfen https://www.python.org adresinden Python yukleyin.
    echo (Yuklerken "Add Python to PATH" kutucugunu isaretlemeyi unutmayin.)
    pause
    exit /b
)

echo [1/2] Kutuphaneler kontrol ediliyor ve yukleniyor...
%PY_CMD% -m pip install --upgrade pip >nul 2>&1
%PY_CMD% -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Kutuphaneler yuklenirken sorun olustu.
    pause
    exit /b
)

echo.
echo [2/2] Ghost Translator baslatiliyor...

:: Sessiz arka plan baslatma (pythonw)
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw main.pyw
) else (
    start "" %PY_CMD% main.pyw
)

echo.
echo ====================================================================
echo     PROGRAM AKTIF!
echo     - Saatin yanindaki ikondan erisebilirsiniz.
echo     - F8: Secili Metni Dinle & Anla
echo     - F9: Chatte Yerinde Ceviri
echo     - CTRL+SHIFT+S: Ekran Kirpma (OCR)
echo     - CTRL+SHIFT+O: Kelime Paneli
echo ====================================================================
timeout /t 3 >nul
exit
