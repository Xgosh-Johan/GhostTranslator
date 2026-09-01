@echo off
cd /d "%~dp0"
echo ===================================================
echo  Ghost Translator - Pushing to GitHub...
echo ===================================================
echo.
git push -u origin main
echo.
echo ===================================================
echo  Islem Tamamlandi!
echo ===================================================
pause
