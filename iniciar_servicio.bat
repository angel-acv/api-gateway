@echo off
REM Uso: iniciar_servicio.bat ventas 5001   |   iniciar_servicio.bat inventario 5003
cd /d "%~dp0servicios"
python servicio.py %1 %2
