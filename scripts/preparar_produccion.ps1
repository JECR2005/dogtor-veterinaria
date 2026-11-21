<#
  S5-12 · Prepara y levanta el entorno con https en Docker: el «servidor del local» de la Tabla 4.2 (D-22, D-25).

  Uso: abrir PowerShell COMO ADMINISTRADOR en la carpeta del proyecto, con Docker Desktop abierto, y ejecutar
      powershell -ExecutionPolicy Bypass -File scripts\preparar_produccion.ps1

  Qué hace (lo que ya está hecho no se repite):
    1. Revisa Docker Desktop, el entorno virtual y .env.
    2. Instala mkcert (con winget) y crea su autoridad local; genera el certificado de dogtor.local en docker\certs.
       Windows pregunta una vez si confía en la autoridad «mkcert»: responda Sí.
    3. Agrega «127.0.0.1 dogtor.local» al archivo hosts de Windows.
    4. En SQL Server habilita TCP/IP en el puerto 1433 y la autenticación de SQL Server (además de la de Windows),
       y reinicia el servicio si cambió algo. Los contenedores no pueden usar su cuenta de Windows.
    5. Crea la cuenta dogtor_web (solo lee y escribe datos) y docker\produccion.env con una clave y una contraseña
       generadas al azar (scripts\preparar_produccion.py), y apunta el monitor de TS-08 a https://dogtor.local.
    6. Construye las imágenes, levanta Nginx y Gunicorn y espera a que https://dogtor.local/salud/ responda.
#>
param([switch]$SinConstruir)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz
$Dominio = "dogtor.local"
function Paso($n, $texto) { Write-Host "`n[$n/6] $texto" -ForegroundColor Cyan }
function Ok($texto) { Write-Host "      OK     $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "      AVISO  $texto" -ForegroundColor Yellow }
function Falla($texto) { Write-Host "      ERROR  $texto" -ForegroundColor Red; exit 1 }

# 1. Requisitos -----------------------------------------------------------------------------------------
Paso 1 "Requisitos"
$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin) { Falla "Abra PowerShell como administrador (clic derecho > Ejecutar como administrador)." }
$Python = Join-Path $Raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { Falla "No existe $Python. Ejecute primero scripts\instalar_local.ps1." }
if (-not (Test-Path (Join-Path $Raiz ".env"))) { Falla "No existe .env en $Raiz." }
$null = & docker version --format "{{.Server.Version}}" 2>$null
if ($LASTEXITCODE -ne 0) { Falla "Docker no responde. Abra Docker Desktop y espere a que diga «Engine running»." }
Ok "Docker Desktop, entorno virtual y .env"
$Conf = @{}
foreach ($linea in Get-Content (Join-Path $Raiz ".env") -Encoding UTF8) {
    if ($linea -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $Conf[$Matches[1]] = $Matches[2].Trim() }
}

# 2. Certificado con mkcert --------------------------------------------------------------------------------
Paso 2 "Certificado local de $Dominio (mkcert)"
$mkcert = Get-Command mkcert -ErrorAction SilentlyContinue
if (-not $mkcert) {
    winget install -e --id FiloSottile.mkcert --accept-source-agreements --accept-package-agreements | Out-Null
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    $mkcert = Get-Command mkcert -ErrorAction SilentlyContinue
    if (-not $mkcert) {
        $mkcert = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet" -Recurse -Filter "mkcert*.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1
    }
    if (-not $mkcert) { Falla "No se pudo instalar mkcert. Instálelo con: winget install FiloSottile.mkcert" }
}
$mkcertExe = if ($mkcert.Source) { $mkcert.Source } else { $mkcert.FullName }
& $mkcertExe -install
$Certs = Join-Path $Raiz "docker\certs"
New-Item -ItemType Directory -Force -Path $Certs | Out-Null
& $mkcertExe -cert-file (Join-Path $Certs "dogtor.pem") -key-file (Join-Path $Certs "dogtor-key.pem") $Dominio localhost 127.0.0.1
if ($LASTEXITCODE -ne 0) { Falla "mkcert no pudo generar el certificado." }
Ok "Certificado en docker\certs (no se sube al repositorio)"

# 3. Archivo hosts ------------------------------------------------------------------------------------------
Paso 3 "Nombre $Dominio en el archivo hosts"
$Hosts = "$env:SystemRoot\System32\drivers\etc\hosts"
if (-not (Select-String -Path $Hosts -Pattern "^\s*127\.0\.0\.1\s+$([regex]::Escape($Dominio))\b" -Quiet)) {
    Add-Content -Path $Hosts -Value "`r`n127.0.0.1`t$Dominio`t# Dogtor (S5-12)" -Encoding ASCII
    Ok "Agregado 127.0.0.1 $Dominio"
} else { Ok "Ya estaba" }

# 4. SQL Server: TCP/IP 1433 y autenticación de SQL Server ------------------------------------------------
Paso 4 "SQL Server: TCP/IP y autenticación de SQL Server"
$hostBd = if ($Conf["DB_HOST"]) { $Conf["DB_HOST"] } else { "localhost\SQLEXPRESS" }
$Instancia = if ($hostBd -match '\\(.+)$') { $Matches[1] } else { "MSSQLSERVER" }
$Servicio = if ($Instancia -eq "MSSQLSERVER") { "MSSQLSERVER" } else { "MSSQL`$$Instancia" }
$Id = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL").$Instancia
if (-not $Id) { Falla "No encontré la instancia $Instancia de SQL Server en este equipo." }
$Clave = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$Id\MSSQLServer"
$cambio = $false
if ((Get-ItemProperty $Clave).LoginMode -ne 2) {
    Set-ItemProperty $Clave -Name LoginMode -Value 2 -Type DWord; $cambio = $true
}
$Tcp = "$Clave\SuperSocketNetLib\Tcp"
if ((Get-ItemProperty $Tcp).Enabled -ne 1) { Set-ItemProperty $Tcp -Name Enabled -Value 1; $cambio = $true }
if ((Get-ItemProperty "$Tcp\IPAll").TcpPort -ne "1433") {
    Set-ItemProperty "$Tcp\IPAll" -Name TcpPort -Value "1433"
    Set-ItemProperty "$Tcp\IPAll" -Name TcpDynamicPorts -Value ""
    $cambio = $true
}
if ($cambio) {
    Restart-Service -Name $Servicio -Force
    Start-Sleep -Seconds 5
    Ok "Cambios aplicados y servicio $Servicio reiniciado"
} else { Ok "Ya estaba: TCP 1433 y autenticación mixta ($Instancia)" }

# 5. Cuenta dogtor_web y docker\produccion.env -------------------------------------------------------------
Paso 5 "Cuenta dogtor_web y variables del contenedor"
& $Python scripts\preparar_produccion.py
if ($LASTEXITCODE -ne 0) { Falla "No se pudo preparar la cuenta de SQL Server (vea el mensaje de arriba)." }

# 6. Contenedores ------------------------------------------------------------------------------------------
Paso 6 "Imágenes y contenedores (la primera vez tarda unos minutos)"
if ($SinConstruir) { docker compose up -d } else { docker compose up -d --build }
if ($LASTEXITCODE -ne 0) { Falla "docker compose no pudo levantar el entorno. Revise: docker compose logs web" }
$listo = $false
foreach ($intento in 1..30) {
    try {
        $r = Invoke-WebRequest -Uri "https://$Dominio/salud/" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { $listo = $true; break }
    } catch { Start-Sleep -Seconds 3 }
}
if (-not $listo) { Falla "https://$Dominio/salud/ no respondió. Revise: docker compose logs web" }
Ok "https://$Dominio responde con certificado válido"

Write-Host "`nListo. Abra https://$Dominio en Chrome o Edge. Los contenedores arrancan solos con Docker Desktop." -ForegroundColor Cyan
Write-Host "El monitor de TS-08 ya revisa https://$Dominio/salud/ (MONITOR_URL en .env)." -ForegroundColor Cyan
