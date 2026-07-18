@echo off
setlocal EnableExtensions

rem Development launcher: PostgreSQL runs in Docker; backend and frontend run locally.
set "PROJECT_DIR=%~dp0"

if not exist "%PROJECT_DIR%docker-compose.yml" (
    echo [ERROR] Khong tim thay docker-compose.yml.
    echo Hay dat file nay trong thu muc smart-menu.
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
    echo [ERROR] Docker Desktop chua san sang. Hay mo Docker Desktop roi thu lai.
    pause
    exit /b 1
)

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Khong tim thay uv. Hay cai uv de chay backend tren may.
    echo Huong dan: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Khong tim thay npm. Hay cai Node.js de chay frontend tren may.
    echo Huong dan: https://nodejs.org/
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

if not exist ".env" (
    echo Dang tao file cau hinh .env cho may nay...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$passwordBytes = New-Object byte[] 32; $secretBytes = New-Object byte[] 48; $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($passwordBytes); $rng.GetBytes($secretBytes); $rng.Dispose(); $password = [Convert]::ToBase64String($passwordBytes); $secret = [Convert]::ToBase64String($secretBytes); $content = \"POSTGRES_USER=smart_menu`nPOSTGRES_PASSWORD=$password`nPOSTGRES_DB=smart_menu`nDB_PORT=5433`nSECRET_KEY=$secret`nCORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`nAPP_BIND_ADDRESS=127.0.0.1`nAPP_PORT=8080`nAI_ENABLED=false`nAI_CONFIG_ENCRYPTION_KEY=`nDEMO_SEED=false`nDEMO_ADMIN_EMAIL=`nDEMO_ADMIN_PASSWORD=`nDEMO_USER_EMAIL=`nDEMO_USER_PASSWORD=\"; Set-Content -Path .env -Value $content -Encoding utf8"
    if errorlevel 1 (
        echo [ERROR] Khong the tao file .env.
        pause
        exit /b 1
    )
)

set "POSTGRES_USER=smart_menu"
set "POSTGRES_DB=smart_menu"
set "DB_PORT=5433"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="POSTGRES_USER" set "POSTGRES_USER=%%B"
    if /I "%%A"=="POSTGRES_DB" set "POSTGRES_DB=%%B"
    if /I "%%A"=="DB_PORT" set "DB_PORT=%%B"
)

echo Dang dam bao frontend/backend Docker da dung...
docker compose --profile demo stop backend frontend >nul 2>nul

echo Dang khoi dong PostgreSQL bang Docker...
docker compose up -d db
if errorlevel 1 (
    echo [ERROR] Khong the khoi dong database.
    pause
    exit /b 1
)

set /a DB_WAIT_COUNT=0
:wait_for_db
docker compose exec -T db pg_isready -U "%POSTGRES_USER%" -d "%POSTGRES_DB%" >nul 2>nul
if not errorlevel 1 goto db_ready
set /a DB_WAIT_COUNT+=1
if %DB_WAIT_COUNT% GEQ 30 (
    echo [ERROR] Database khong san sang sau 60 giay.
    docker compose logs db
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait_for_db

:db_ready
echo Database da san sang tai 127.0.0.1:%DB_PORT%.

set "APP_ENV=development"
set "POSTGRES_HOST=localhost"
set "POSTGRES_PORT=%DB_PORT%"
set "CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173"

echo Dang cai/cap nhat dependency backend...
pushd "%PROJECT_DIR%backend"
uv sync --extra dev
if errorlevel 1 (
    popd
    echo [ERROR] Cai dependency backend that bai.
    pause
    exit /b 1
)

echo Dang cap nhat database...
uv run python scripts\apply_migrations.py
if errorlevel 1 (
    popd
    echo [ERROR] Migration database that bai.
    pause
    exit /b 1
)
uv run python scripts\seed_admin.py
if errorlevel 1 (
    popd
    echo [ERROR] Tao tai khoan admin that bai. Kiem tra DEMO_ADMIN_EMAIL va DEMO_ADMIN_PASSWORD trong .env.
    pause
    exit /b 1
)
popd

if not exist "%PROJECT_DIR%frontend\node_modules" (
    echo Dang cai dependency frontend...
    pushd "%PROJECT_DIR%frontend"
    call npm ci
    if errorlevel 1 (
        popd
        echo [ERROR] Cai dependency frontend that bai.
        pause
        exit /b 1
    )
    popd
)

echo Dang mo backend va frontend tren hai cua so rieng...
start "Smart Menu Backend" /D "%PROJECT_DIR%backend" cmd /k "uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001"
start "Smart Menu Frontend" /D "%PROJECT_DIR%frontend" cmd /k "npm run dev -- --host 127.0.0.1 --strictPort"

echo Dang cho frontend san sang...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddSeconds(60); while ((Get-Date) -lt $deadline) { try { $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Seconds 1 }; exit 1"
if errorlevel 1 (
    echo [WARNING] Frontend chua phan hoi tai http://localhost:5173.
    echo Hay xem loi trong hai cua so Backend va Frontend vua mo.
    pause
    exit /b 1
)

echo.
echo Smart Menu dang chay o che do local:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8001
echo   Database: 127.0.0.1:%DB_PORT% ^(Docker^)
start "Smart Menu" "http://localhost:5173"
echo Dong hai cua so Backend/Frontend de dung app.
pause
