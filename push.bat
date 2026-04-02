@echo off
cd /d "C:\Users\HalvardNordang\Documents\geopolitisk-modell"
echo.
echo === Pusher index.html til GitHub ===
git add -f index.html
for /f "tokens=1-3 delims=." %%a in ("%date%") do set DAG=%%a&set MND=%%b&set AAR=%%c
for /f "tokens=1-2 delims=:" %%a in ("%time%") do set TIM=%%a&set MIN=%%b
set MELDING=Oppdatering %DAG%.%MND%.%AAR% kl %TIM%:%MIN%
git commit -m "%MELDING%"
git push
echo.
echo === Ferdig! ===
echo.
pause
