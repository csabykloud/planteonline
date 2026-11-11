@echo off
title PlanteOnline.ro - Publikus Megoszto Link (Cloudflare Tunnel)
echo ====================================================================
echo   1. PlanteOnline helyi szerver ellenorzese / inditasa (port 5000)
echo ====================================================================
netstat -ano | findstr :5000 >nul
if %errorlevel% neq 0 (
    echo Helyi Flask szerver inditasa kulon ablakban...
    start "PlanteOnline Local Server" cmd /c "cd /d "%~dp0" && python app.py"
    timeout /t 3 /nobreak >nul
) else (
    echo A helyi szerver mar fut a http://127.0.0.1:5000 cimen!
)

echo.
echo ====================================================================
echo   2. Cloudflare Tunnel inditasa (Masold ki a .trycloudflare.com linket!)
echo ====================================================================
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5000
pause
