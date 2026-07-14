@echo off
setlocal EnableExtensions

rem One-click launcher for Windows users with Docker Desktop installed.
set "PROJECT_DIR=%~dp0"

if not exist "%PROJECT_DIR%docker-compose.yml" (
    echo [ERROR] Khong tim thay docker-compose.yml.
    echo Hay chay file nay tu thu muc smart-menu.
    pause
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Khong tim thay Docker. Hay cai va mo Docker Desktop truoc.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Docker Desktop chua san sang. Hay mo Docker Desktop, doi den khi no chay roi thu lai.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

set "APP_PORT=8080"

if not exist ".env" (
    echo Dang tao file cau hinh .env cho may nay...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$passwordBytes = New-Object byte[] 32; $secretBytes = New-Object byte[] 48; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($passwordBytes); $rng.GetBytes($secretBytes); $rng.Dispose(); $password = [Convert]::ToBase64String($passwordBytes); $secret = [Convert]::ToBase64String($secretBytes); $content = \"POSTGRES_USER=smart_menu`nPOSTGRES_PASSWORD=$password`nPOSTGRES_DB=smart_menu`nDB_PORT=5433`nSECRET_KEY=$secret`nCORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080`nAPP_BIND_ADDRESS=127.0.0.1`nAPP_PORT=8080`nAI_ENABLED=false`nAI_CONFIG_ENCRYPTION_KEY=`nDEMO_SEED=false`nDEMO_ADMIN_EMAIL=`nDEMO_ADMIN_PASSWORD=`nDEMO_USER_EMAIL=`nDEMO_USER_PASSWORD=\"; Set-Content -Path .env -Value $content -Encoding utf8"
    if errorlevel 1 (
        echo [ERROR] Khong the tao file .env.
        pause
        exit /b 1
    )
)

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="APP_PORT" set "APP_PORT=%%B"
)
set "APP_URL=http://localhost:%APP_PORT%"

echo Dang tai/dung image va khoi dong Smart Menu. Lan dau tien co the mat vai phut...
docker compose --profile demo up --build -d
if errorlevel 1 (
    echo [ERROR] Khoi dong app that bai. Xem loi chi tiet bang lenh:
    echo cd /d "%PROJECT_DIR%" ^&^& docker compose logs
    pause
    exit /b 1
)

echo.
echo Smart Menu da khoi dong tai: %APP_URL%
start "Smart Menu" "%APP_URL%"
echo De dung app sau nay, chay: cd /d "%PROJECT_DIR%" ^&^& docker compose --profile demo down
pause
