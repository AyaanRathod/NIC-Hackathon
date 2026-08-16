@echo off
setlocal
cd /d %~dp0
echo Stopping any existing containers...
docker compose down
echo.
echo Building and launching Halal Income and Zakat Calculator (Fresh Build)...
docker compose up --build --force-recreate
