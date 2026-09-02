@echo off
chcp 65001 >nul
title Ghost Translator - Tam Otomatik Kurulum ve Baslatici
color 0A

cd /d "%~dp0"

echo ====================================================================
echo      GHOST TRANSLATOR - TAM OTOMATIK KURULUM SISTEMI
echo ====================================================================
echo.

set "PY_EXE="

:: 1. Gercek Python yollarini kontrol et (Store sahte kisayollarini atla)
for /d %%I in ("%LocalAppData%\Programs\Python\Python*") do (
    if exist "%%I\python.exe" set "PY_EXE=%%I\python.exe"
)

if not defined PY_EXE (
    for /d %%I in ("C:\Python*") do (
        if exist "%%I\python.exe" set "PY_EXE=%%I\python.exe"
    )
)

:: 2. Standart komutlari test et (Eger gercekse calisir)
if not defined PY_EXE (
    py -0 >nul 2>&1 && set "PY_EXE=py"
)

:: 3. Bilgisayarda Python hic yoksa: Otomatik indir ve kur
if not defined PY_EXE (
    echo [BILGI] Bilgisayarda Python tespit edilemedi.
    echo [1/3] Python 3.11 arka planda indiriliyor...
    
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $wc = New-Object System.Net.WebClient; $wc.DownloadFile('https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe', 'python_installer.exe')"
    
    if not exist "python_installer.exe" (
        color 0C
        echo [HATA] Python kurulum dosyasi indirilemedi! Internet baglantinizi kontrol edin.
        pause
        exit /b
    )
    
    echo [2/3] Python sisteme sessizce kuruluyor, lutfen 30-40 saniye bekleyin...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
    del python_installer.exe
    
    :: Yeni kurulan Python'u bul
    for /d %%I in ("%LocalAppData%\Programs\Python\Python311*") do (
        if exist "%%I\python.exe" set "PY_EXE=%%I\python.exe"
    )
)

if not defined PY_EXE (
    color 0C
    echo [HATA] Python kurulumu tamamlanamadi.
    pause
    exit /b
)

echo [BILGI] Kullanilan Python: %PY_EXE%
echo.
echo [3/3] Gerekli yapay zeka, cevirmen ve ses paketleri yukleniyor...
"%PY_EXE%" -m pip install --upgrade pip
"%PY_EXE%" -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Kutuphaneler yuklenirken sorun yasandi!
    pause
    exit /b
)

echo.
echo ====================================================================
echo      KURULUM TAMAMLANDI! PROGRAM BASLATILIYOR...
echo ====================================================================

:: Programi calistir
set "PYW_EXE=%PY_EXE:python.exe=pythonw.exe%"
if exist "%PYW_EXE%" (
    start "" "%PYW_EXE%" main.pyw
) else (
    start "" "%PY_EXE%" main.pyw
)

timeout /t 3 >nul
exit
