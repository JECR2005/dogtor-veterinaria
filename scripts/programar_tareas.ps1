<#
  S5-08 · Programa las tareas diarias de Dogtor en el Programador de tareas de Windows (RNF-04, RF-09, RNF-06).

  SQL Server Express no tiene el Agente SQL (D-09), así que las tareas viven en el Programador de tareas, en la
  carpeta «Dogtor»:
    - Respaldo diario            todos los días a las 22:00   python scripts\tarea.py respaldo
    - Recordatorios del día      lunes a sábado a las 08:30   python scripts\tarea.py recordatorios
    - Monitor de disponibilidad  lunes a sábado, cada 5 min de 09:00 a 19:00   python scripts\tarea.py monitor
  Corren con su cuenta de Windows mientras tiene la sesión abierta, sin ventana (pythonw.exe). Si el equipo
  estaba apagado a la hora del respaldo o de los recordatorios, se ejecutan en cuanto se enciende. Lo que pasa
  queda en logs\tareas.log y logs\disponibilidad.csv.

  Uso: abrir PowerShell COMO ADMINISTRADOR en la carpeta del proyecto y ejecutar
      powershell -ExecutionPolicy Bypass -File scripts\programar_tareas.ps1           # crea o actualiza
      powershell -ExecutionPolicy Bypass -File scripts\programar_tareas.ps1 -Probar   # y las ejecuta una vez
      powershell -ExecutionPolicy Bypass -File scripts\programar_tareas.ps1 -Quitar   # las elimina
  Como administrador también da permiso de escritura en RESPALDO_DIR a la cuenta del servicio de SQL Server.
#>
param(
    [switch]$Probar,
    [switch]$Quitar
)

$ErrorActionPreference = "Stop"
$Carpeta = "\Dogtor\"
$Raiz = Split-Path -Parent $PSScriptRoot
function Ok($texto) { Write-Host "  OK     $texto" -ForegroundColor Green }
function Aviso($texto) { Write-Host "  AVISO  $texto" -ForegroundColor Yellow }
function Falla($texto) { Write-Host "  ERROR  $texto" -ForegroundColor Red; exit 1 }

$esAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $esAdmin) { Falla "Abra PowerShell como administrador (clic derecho > Ejecutar como administrador)." }

if ($Quitar) {
    Get-ScheduledTask -TaskPath $Carpeta -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    Ok "Tareas de Dogtor eliminadas."
    exit 0
}

# 1. Entorno virtual y .env ----------------------------------------------------------------------
$Pythonw = Join-Path $Raiz ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $Pythonw)) { Falla "No existe $Pythonw. Ejecute primero scripts\instalar_local.ps1." }
$Conf = @{}
$ArchivoEnv = Join-Path $Raiz ".env"
if (-not (Test-Path $ArchivoEnv)) { Falla "No existe .env en $Raiz." }
foreach ($linea in Get-Content $ArchivoEnv -Encoding UTF8) {
    if ($linea -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $Conf[$Matches[1]] = $Matches[2].Trim() }
}
Ok "Proyecto en $Raiz"

# 2. Carpeta de respaldos con permiso para el servicio de SQL Server ------------------------------
$Respaldos = $Conf["RESPALDO_DIR"]
if (-not $Respaldos) { Falla "Defina RESPALDO_DIR en .env (por ejemplo C:\DogtorRespaldos)." }
New-Item -ItemType Directory -Force -Path $Respaldos | Out-Null
$hostBd = if ($Conf["DB_HOST"]) { $Conf["DB_HOST"] } else { "localhost\SQLEXPRESS" }
$servicio = if ($hostBd -match '\\(.+)$') { "NT SERVICE\MSSQL`$$($Matches[1])" } else { "NT SERVICE\MSSQLSERVER" }
& icacls $Respaldos /grant "${servicio}:(OI)(CI)M" | Out-Null
if ($LASTEXITCODE -eq 0) { Ok "$servicio puede escribir en $Respaldos" }
else { Aviso "No se pudo dar permiso a $servicio en $Respaldos; el respaldo podría fallar con «Access is denied»." }
if (-not $Conf["RESPALDO_COPIA_EXTERNA"]) {
    Aviso "RESPALDO_COPIA_EXTERNA está vacía: RNF-04 pide una copia fuera del equipo (USB, OneDrive...)."
}
New-Item -ItemType Directory -Force -Path (Join-Path $Raiz "logs") | Out-Null

# 3. Tareas ------------------------------------------------------------------------------------------
$Usuario = "$env:USERDOMAIN\$env:USERNAME"
$Principal = New-ScheduledTaskPrincipal -UserId $Usuario -LogonType Interactive -RunLevel Limited
$Dias = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")

function Accion($nombre) {
    New-ScheduledTaskAction -Execute $Pythonw -Argument "scripts\tarea.py $nombre" -WorkingDirectory $Raiz
}
function Ajustes([switch]$AlEncender, [int]$Minutos = 120) {
    $parametros = @{
        AllowStartIfOnBatteries   = $true
        DontStopIfGoingOnBatteries = $true
        MultipleInstances         = "IgnoreNew"
        ExecutionTimeLimit        = (New-TimeSpan -Minutes $Minutos)
    }
    if ($AlEncender) { $parametros["StartWhenAvailable"] = $true }
    New-ScheduledTaskSettingsSet @parametros
}

$respaldo = New-ScheduledTaskTrigger -Daily -At "22:00"
Register-ScheduledTask -TaskPath $Carpeta -TaskName "Respaldo diario" -Force -Principal $Principal `
    -Action (Accion "respaldo") -Trigger $respaldo -Settings (Ajustes -AlEncender) `
    -Description "RNF-04: respaldo completo verificado, copia externa y 30 días de conservación (S5-08)." | Out-Null
Ok "Respaldo diario: todos los días a las 22:00"

$recordatorios = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Dias -At "08:30"
Register-ScheduledTask -TaskPath $Carpeta -TaskName "Recordatorios del dia" -Force -Principal $Principal `
    -Action (Accion "recordatorios") -Trigger $recordatorios -Settings (Ajustes -AlEncender -Minutos 15) `
    -Description "RF-09: genera la lista de recordatorios antes de que llegue el personal (S5-08)." | Out-Null
Ok "Recordatorios del día: lunes a sábado a las 08:30"

$monitor = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Dias -At "09:00"
$monitor.Repetition = (New-ScheduledTaskTrigger -Once -At "09:00" -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Hours 10)).Repetition
Register-ScheduledTask -TaskPath $Carpeta -TaskName "Monitor de disponibilidad" -Force -Principal $Principal `
    -Action (Accion "monitor") -Trigger $monitor -Settings (Ajustes -Minutos 2) `
    -Description "RNF-06 y TS-08: revisa /salud/ cada 5 minutos en el horario de atención (S5-10, D-22)." | Out-Null
Ok "Monitor de disponibilidad: lunes a sábado, cada 5 minutos de 09:00 a 19:00"

# 4. Prueba opcional ---------------------------------------------------------------------------------
if ($Probar) {
    foreach ($tarea in "Respaldo diario", "Recordatorios del dia") {
        Start-ScheduledTask -TaskPath $Carpeta -TaskName $tarea
        do { Start-Sleep -Seconds 2 } while ((Get-ScheduledTask -TaskPath $Carpeta -TaskName $tarea).State -eq "Running")
        $info = Get-ScheduledTaskInfo -TaskPath $Carpeta -TaskName $tarea
        if ($info.LastTaskResult -eq 0) { Ok "$tarea se ejecutó bien." }
        else { Aviso "$tarea terminó con código $($info.LastTaskResult). Revise logs\tareas.log." }
    }
}

Write-Host ""
Get-ScheduledTask -TaskPath $Carpeta | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskPath $Carpeta -TaskName $_.TaskName
    "{0,-28} próxima: {1}" -f $_.TaskName, $info.NextRunTime
}
Write-Host "`nListo. Bitácora de las tareas: logs\tareas.log" -ForegroundColor Cyan
