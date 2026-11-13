<#
  S1-02 · Instala el entorno local de Dogtor en Windows (Tabla 4.3, entorno "Local").

  Uso, desde la carpeta del proyecto en PowerShell:
      powershell -ExecutionPolicy Bypass -File scripts\instalar_local.ps1
  Opcional: -Servidor "localhost\SQLEXPRESS"   (por defecto usa MSI\SQLEXPRESS)

  Qué hace (se puede ejecutar varias veces; lo que ya existe no se repite):
    1. Revisa Python 3.10 a 3.13.
    2. Revisa el ODBC Driver for SQL Server (18 o, si no hay, 17).
    3. Crea el entorno virtual .venv e instala requirements-dev.txt.
    4. Crea el archivo .env con autenticación de Windows y una clave secreta nueva.
    5. Revisa la conexión a SQL Server y que existan las 26 tablas (si no, ejecuta bd/01 y bd/02).
    6. Crea las tablas propias de Django (migrate).
    7. Carga los datos ficticios (cargar_datos_prueba) y corre las pruebas de humo.
#>
param(
    [string]$Servidor = "MSI\SQLEXPRESS"
)

# "Continue": en PowerShell 5.1 una advertencia escrita por un programa en stderr no debe detener el script;
# cada paso revisa $LASTEXITCODE.
$ErrorActionPreference = "Continue"
$Raiz = Split-Path $PSScriptRoot -Parent
Set-Location $Raiz

function Paso($n, $texto) { Write-Host "`n[$n/7] $texto" -ForegroundColor Cyan }
function Ok($texto) { Write-Host "      OK  $texto" -ForegroundColor Green }
function Falla($texto) { Write-Host "      ERROR  $texto" -ForegroundColor Red; exit 1 }

# 1. Python ----------------------------------------------------------------------
Paso 1 "Python"
$python = $null       # ejecutable
$pyArgs = @()         # argumentos previos (por ejemplo -3.12 para el lanzador py)
foreach ($candidato in @("py -3.12", "py -3.13", "py -3.11", "python")) {
    $partes = @($candidato -split " ")
    $exe = $partes[0]
    $extra = @($partes | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $version = (& $exe @extra --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $version -match "Python 3\.(1[0-3])\.") { $python = $exe; $pyArgs = $extra; break }
}
if (-not $python) {
    Falla "No se encontró Python 3.10 a 3.13. Instálalo desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH')."
}
Ok $version

# 2. ODBC Driver ------------------------------------------------------------------
Paso 2 "ODBC Driver for SQL Server"
$controladores = @(Get-OdbcDriver -Platform "64-bit" | Where-Object { $_.Name -match "^ODBC Driver (1[78]) for SQL Server$" } |
    Select-Object -ExpandProperty Name | Sort-Object -Descending)
if ($controladores.Count -eq 0) {
    Falla "No hay ODBC Driver 17 ni 18. Descarga el 18 de https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server y vuelve a ejecutar."
}
$driver = $controladores[0]
Ok $driver

# 3. Entorno virtual y dependencias --------------------------------------------------
Paso 3 "Entorno virtual .venv y dependencias"
$venvPython = Join-Path $Raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & $python @pyArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { Falla "No se pudo crear .venv" }
}
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements-dev.txt --quiet
if ($LASTEXITCODE -ne 0) { Falla "pip no pudo instalar requirements-dev.txt" }
Ok "Dependencias instaladas"

# 4. Archivo .env ------------------------------------------------------------------
Paso 4 "Archivo .env"
$rutaEnv = Join-Path $Raiz ".env"
if (Test-Path $rutaEnv) {
    Ok ".env ya existe; no se modifica"
} else {
    $clave = & $venvPython -c "import secrets; print(secrets.token_urlsafe(50))"
    $respaldos = "C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\Backup"
    $lineas = Get-Content (Join-Path $Raiz ".env.example") -Encoding UTF8 | ForEach-Object {
        switch -Regex ($_) {
            "^DJANGO_SECRET_KEY=" { "DJANGO_SECRET_KEY=$clave"; break }
            "^DB_HOST="           { "DB_HOST=$Servidor"; break }
            "^DB_PUERTO="         { "DB_PUERTO="; break }
            "^DB_USUARIO="        { "DB_USUARIO="; break }      # vacío = autenticación de Windows
            "^DB_CONTRASENA="     { "DB_CONTRASENA="; break }
            "^DB_DRIVER="         { "DB_DRIVER=$driver"; break }
            "^RESPALDO_DIR="      { "RESPALDO_DIR=$respaldos"; break }
            default               { $_ }
        }
    }
    [System.IO.File]::WriteAllLines($rutaEnv, $lineas, (New-Object System.Text.UTF8Encoding $false))
    Ok ".env creado (servidor $Servidor, autenticación de Windows, $driver)"
}

# 5. Conexión y tablas de bd/ ----------------------------------------------------------
Paso 5 "Conexión a SQL Server y tablas del sistema"
$tablas = & $venvPython manage.py shell -c "from django.db import connection; t = set(connection.introspection.table_names()); print(sum(n in t for n in ['cliente','mascota','cita','venta','lote','usuario']))" 2>&1
if ($LASTEXITCODE -ne 0) { Falla "No se pudo conectar a $Servidor. Revisa que el servicio SQL Server (SQLEXPRESS) esté iniciado.`n$tablas" }
if ("$tablas".Trim() -ne "6") {
    Write-Host "      Las tablas no existen en la base Dogtor; ejecutando bd/01_tablas.sql y bd/02_vistas.sql..."
    & $venvPython bd\ejecutar.py
    if ($LASTEXITCODE -ne 0) { Falla "No se pudieron crear las tablas (¿existe la base Dogtor? ver bd/00_crear_base_y_usuario.sql)" }
}
Ok "Base Dogtor con sus tablas"

# 6. Tablas propias de Django ----------------------------------------------------------
Paso 6 "migrate (sesiones, historial de migraciones, tipos de contenido)"
& $venvPython manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { Falla "migrate falló" }
Ok "Migraciones aplicadas"

# 7. Datos ficticios y pruebas de humo --------------------------------------------------
Paso 7 "Datos ficticios y pruebas de humo"
& $venvPython manage.py cargar_datos_prueba
if ($LASTEXITCODE -ne 0) { Falla "cargar_datos_prueba falló" }
& $venvPython -m pytest -m unidad -q
if ($LASTEXITCODE -ne 0) { Falla "Fallaron pruebas de unidad" }
Ok "Listo"

Write-Host "`nEntorno local instalado." -ForegroundColor Green
Write-Host "Para iniciar el sistema:" -ForegroundColor Green
Write-Host "    .venv\Scripts\python.exe manage.py runserver"
Write-Host "y abre http://127.0.0.1:8000/  ·  http://127.0.0.1:8000/salud/  ·  http://127.0.0.1:8000/admin-local/"
Write-Host "Cuentas de prueba: administrador, veterinario, estilista, recepcion (contraseña en DATOS_PRUEBA_CONTRASENA de .env)."
