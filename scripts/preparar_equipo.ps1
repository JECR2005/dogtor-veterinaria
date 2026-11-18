<#
  Prepara un equipo nuevo con Windows para trabajar en Dogtor (instala los programas que pide el README).

  Uso: abrir PowerShell COMO ADMINISTRADOR y ejecutar
      powershell -ExecutionPolicy Bypass -File scripts\preparar_equipo.ps1
  o, si todavía no se ha clonado el repositorio (es público), descargarlo y ejecutarlo:
      irm https://raw.githubusercontent.com/JECR2005/dogtor-veterinaria/develop/scripts/preparar_equipo.ps1 -OutFile $env:TEMP\preparar_equipo.ps1
      powershell -ExecutionPolicy Bypass -File $env:TEMP\preparar_equipo.ps1

  Qué hace (lo que ya está instalado no se repite):
    1. Revisa que winget exista y que la ventana sea de administrador.
    2. Instala Git, Python 3.12, SQL Server 2022 Express (si no hay ya una instancia), ODBC Driver 18 y SSMS.
    3. Revisa que el servicio de SQL Server (SQLEXPRESS o la instancia predeterminada) esté iniciado y en
       arranque automático.
    4. Clona el repositorio en Documentos\dogtor-veterinaria (rama develop), si no existe.
  Después: cerrar esta ventana, abrir PowerShell NORMAL en esa carpeta y ejecutar scripts\instalar_local.ps1.
#>
param(
    [string]$Carpeta = (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "dogtor-veterinaria"),
    [switch]$SinSSMS
)

$ErrorActionPreference = "Continue"
function Paso($n, $texto) { Write-Host "`n[$n/4] $texto" -ForegroundColor Cyan }
function Ok($texto) { Write-Host "      OK  $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "      AVISO  $texto" -ForegroundColor Yellow }
function Falla($texto) { Write-Host "      ERROR  $texto" -ForegroundColor Red; exit 1 }

# 1. Requisitos de esta ventana ----------------------------------------------------
Paso 1 "Permisos y winget"
$esAdministrador = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdministrador) { Falla "Abre PowerShell con clic derecho > Ejecutar como administrador y vuelve a ejecutar." }
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Falla "No está winget. Instala o actualiza 'Instalador de aplicación' desde Microsoft Store y vuelve a ejecutar."
}
Ok "Administrador y winget disponibles"

# 2. Programas ------------------------------------------------------------------------
Paso 2 "Programas (puede tardar varios minutos; SQL Server es el más pesado)"
$programas = @(
    @{ Id = "Git.Git"; Nombre = "Git" },
    @{ Id = "Python.Python.3.12"; Nombre = "Python 3.12" },
    @{ Id = "Microsoft.SQLServer.2022.Express"; Nombre = "SQL Server 2022 Express" },
    @{ Id = "Microsoft.msodbcsql.18"; Nombre = "ODBC Driver 18 for SQL Server" }
)
if (-not $SinSSMS) { $programas += @{ Id = "Microsoft.SQLServerManagementStudio"; Nombre = "SQL Server Management Studio" } }

# Si ya hay una instancia de SQL Server (con nombre o predeterminada), no se instala otra
$instancias = @(Get-Service -Name 'MSSQL$SQLEXPRESS', 'MSSQLSERVER' -ErrorAction SilentlyContinue)
if ($instancias.Count -gt 0) {
    $programas = @($programas | Where-Object { $_.Id -ne "Microsoft.SQLServer.2022.Express" })
    Ok "SQL Server ya estaba instalado ($($instancias[0].DisplayName))"
}

foreach ($p in $programas) {
    $lista = winget list --id $p.Id --exact --accept-source-agreements 2>$null | Out-String
    if ($lista -match [regex]::Escape($p.Id)) { Ok "$($p.Nombre) ya estaba instalado"; continue }
    Write-Host "      Instalando $($p.Nombre)..."
    winget install --id $p.Id --exact --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { Aviso "winget devolvió $LASTEXITCODE al instalar $($p.Nombre). Revisa el mensaje; si ya quedó instalado, continúa." }
    else { Ok "$($p.Nombre) instalado" }
}

# Los programas recién instalados aún no están en el PATH de esta ventana
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

# 3. Servicio de SQL Server -------------------------------------------------------------
Paso 3 "Servicio de SQL Server"
# Instancia con nombre SQLEXPRESS o instancia predeterminada MSSQLSERVER: cualquiera sirve
$servicio = Get-Service -Name 'MSSQL$SQLEXPRESS', 'MSSQLSERVER' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $servicio) {
    Falla ("No hay SQL Server en este equipo. El instalador automático falla si el idioma de Windows y el formato " +
        "regional no coinciden (código 1009). Instala SQL Server 2022 Express a mano desde " +
        "https://www.microsoft.com/es-mx/sql-server/sql-server-downloads (tipo Básica; acepta continuar en inglés) " +
        "y vuelve a ejecutar.")
}
Set-Service -Name $servicio.Name -StartupType Automatic
if ($servicio.Status -ne "Running") { Start-Service -Name $servicio.Name }
$servidor = if ($servicio.Name -eq "MSSQLSERVER") { "localhost" } else { "localhost\SQLEXPRESS" }
Ok "$($servicio.DisplayName) iniciado y en arranque automático (servidor: $servidor)"

# 4. Repositorio ----------------------------------------------------------------------------
Paso 4 "Repositorio en $Carpeta"
if (Test-Path (Join-Path $Carpeta ".git")) {
    Ok "Ya estaba clonado"
} else {
    git clone --branch develop https://github.com/JECR2005/dogtor-veterinaria.git $Carpeta
    if ($LASTEXITCODE -ne 0) { Falla "No se pudo clonar el repositorio." }
    Ok "Clonado (rama develop)"
}

Write-Host "`nEquipo listo." -ForegroundColor Green
Write-Host "Ahora CIERRA esta ventana, abre PowerShell normal (sin administrador) y ejecuta:" -ForegroundColor Green
Write-Host "    cd `"$Carpeta`""
Write-Host "    powershell -ExecutionPolicy Bypass -File scripts\instalar_local.ps1"
