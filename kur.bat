@echo off
schtasks /create /sc daily /st 20:00 /tn "MangaAnimeBildirici" /tr "\"%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe\" \"%~dp0bildirici.py\"" /f
powershell -NoProfile -Command "Set-ScheduledTask -TaskName MangaAnimeBildirici -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries) | Out-Null"
echo Kuruldu. Kaldirmak icin: schtasks /delete /tn "MangaAnimeBildirici" /f
pause
