# Levanta el prototipo SIN Docker (PostgreSQL local ya instalado). Uso, desde la raíz del repo:
#   powershell -ExecutionPolicy Bypass -File scripts\dev.ps1            # prepara, migra, carga seed si está vacío y levanta
#   powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 -ResetSeed # además recarga los datos de demo
# Si el puerto 8000 (API) o 5173 (frontend) está ocupado por otra aplicación, se usa el siguiente libre.
param([switch]$ResetSeed, [int]$PuertoApi = 8000, [int]$PuertoWeb = 5173)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$back = Join-Path $raiz 'backend'
$front = Join-Path $raiz 'frontend'

function Puerto-Libre([int]$desde) {
  $p = $desde
  while (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue) { $p++ }
  return $p
}

if (-not (Test-Path (Join-Path $back '.env'))) {
  Copy-Item (Join-Path $raiz '.env.example') (Join-Path $back '.env')
  Write-Host 'Se creó backend\.env desde .env.example. Revisa DATABASE_URL y JWT_SECRET.' -ForegroundColor Yellow
}
$py = Join-Path $back '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  Write-Host 'Creando entorno de Python...'
  python -m venv (Join-Path $back '.venv')
  & $py -m pip install -q -r (Join-Path $back 'requirements-dev.txt')
}
if (-not (Test-Path (Join-Path $front 'node_modules'))) {
  Write-Host 'Instalando dependencias del frontend...'
  Push-Location $front; npm install; Pop-Location
}

Push-Location $back
& $py -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { Pop-Location; throw 'No se pudo migrar la base de datos. ¿Está corriendo el servicio de PostgreSQL?' }
if ($ResetSeed) { & $py -m app.seed --reset } else { & $py -m app.seed }

$api = Puerto-Libre $PuertoApi
if ($api -ne $PuertoApi) {
  Write-Host "El puerto $PuertoApi está ocupado por otra aplicación; la API usará el puerto $api." -ForegroundColor Yellow
}
$proc = Start-Process -FilePath $py -ArgumentList '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$api" -PassThru -NoNewWindow
Pop-Location

# Espera a que responda NUESTRA API (no otra que esté en el mismo puerto)
$lista = $false
for ($i = 0; $i -lt 30 -and -not $lista; $i++) {
  Start-Sleep -Milliseconds 500
  try { $lista = (Invoke-RestMethod "http://127.0.0.1:$api/api/salud" -TimeoutSec 3).estado -eq 'ok' } catch { }
}
if (-not $lista) {
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  throw "La API no respondió en http://127.0.0.1:$api/api/salud. Revisa los mensajes de arriba."
}

$web = Puerto-Libre $PuertoWeb
$env:VITE_API_PROXY = "http://127.0.0.1:$api"   # IP explícita: "localhost" puede resolver a IPv6 (::1)
Write-Host "`nAPI:      http://localhost:$api/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:$web  (Ctrl+C para detener todo)`n" -ForegroundColor Green
try {
  Push-Location $front
  npm run dev -- --port $web --strictPort
} finally {
  Pop-Location
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}
