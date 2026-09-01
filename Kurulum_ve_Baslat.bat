@echo off
chcp 65001 >nul
title Ghost Translator & AI Desktop Co-Pilot - Kurulum ve Başlatıcı
color 0A

echo ======================================================================
echo    GHOST TRANSLATOR ^& AI DESKTOP CO-PILOT - OTOMATİK KURULUM
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Bilgisayarınızda Python yüklü bulunamadı!
    echo Lütfen https://www.python.org adresinden Python 3.9+ yükleyin.
    echo (Yüklerken "Add Python to PATH" seçeneğini işaretlemeyi unutmayın.)
    echo.
    pause
    exit /b
)

echo [1/2] Gerekli Python kütüphaneleri yükleniyor (PyQt5, Edge-TTS, vb.)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Kütüphaneler yüklenirken bir sorun oluştu!
    pause
    exit /b
)

echo.
echo [2/2] Ghost Translator başarıyla kuruldu! Arka planda başlatılıyor...
start pythonw main.pyw

echo.
echo ======================================================================
echo    PROGRAM AKTİF! 
echo    - Saatin yanındaki yeşil ikondan ayarlara erişebilirsiniz.
echo    - F8: Seçili Metni Çevir ^& Dinle
echo    - F9: Chatte Yerinde Çeviri
echo    - CTRL+SHIFT+S: Ekran Kırpma (OCR)
echo ======================================================================
timeout /t 4 >nul
exit
