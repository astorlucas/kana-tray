#Requires -Version 5.1
<#
.SYNOPSIS
    Instalador de Kana Tray para Windows 10/11.

.DESCRIPTION
    Equivalente de install.sh. Resuelve Python, instala PyQt6 (en un entorno
    virtual si hace falta), crea el acceso directo en el menú Inicio y, si se
    pide, el arranque automático en la clave Run del usuario.

    No necesita permisos de administrador: todo queda en el perfil del usuario.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Venv -Autostart
    .\install.ps1 -Uninstall

.NOTES
    Si PowerShell bloquea el script:
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>
param(
    [switch]$Venv,        # forzar entorno virtual en .venv
    [switch]$System,      # usar el Python del sistema (exige PyQt6 instalado)
    [switch]$Autostart,   # además arrancar con la sesión
    [switch]$Uninstall    # quitar acceso directo, autostart y .venv
)

$ErrorActionPreference = 'Stop'

$AppDir     = $PSScriptRoot
$Script     = Join-Path $AppDir 'kana_tray.py'
$VenvDir    = Join-Path $AppDir '.venv'
$IcoPath    = Join-Path $AppDir 'kana-tray.ico'
$TablePath  = Join-Path $AppDir 'KANA.md'
$StartMenu  = [Environment]::GetFolderPath('Programs')
$Shortcut   = Join-Path $StartMenu 'Kana Tray.lnk'
$RunKey     = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$RunName    = 'Kana Tray'
$MinMinor   = 9

function Write-Step($msg) { Write-Host "  $msg" }
function Write-Ok($msg)   { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Stop-With($msg) {
    Write-Host ''
    Write-Host "  [x] $msg" -ForegroundColor Red
    Write-Host ''
    exit 1
}

# --------------------------------------------------------------------------- #
# Desinstalar
# --------------------------------------------------------------------------- #
if ($Uninstall) {
    Write-Host ''
    Write-Host '  Desinstalando Kana Tray'
    Write-Host ''

    if (Test-Path $Shortcut) {
        Remove-Item $Shortcut -Force
        Write-Ok "borrado $Shortcut"
    } else {
        Write-Step "no estaba $Shortcut"
    }

    if ($null -ne (Get-ItemProperty -Path $RunKey -Name $RunName -ErrorAction SilentlyContinue)) {
        Remove-ItemProperty -Path $RunKey -Name $RunName
        Write-Ok 'quitado el arranque automático'
    } else {
        Write-Step 'no estaba el arranque automático'
    }

    foreach ($path in @($VenvDir, $IcoPath)) {
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
            Write-Ok "borrado $path"
        }
    }

    Write-Host ''
    Write-Step "Tus estadísticas siguen en $env:APPDATA\kana-tray"
    Write-Step 'Borrá esa carpeta a mano si tampoco las querés conservar.'
    Write-Host ''
    exit 0
}

# --------------------------------------------------------------------------- #
# Chequeos
# --------------------------------------------------------------------------- #
Write-Host ''
Write-Host '  Instalando Kana Tray'
Write-Host ''

if (-not (Test-Path $Script)) {
    Stop-With 'No encuentro kana_tray.py; corré el script desde el repo.'
}
if (-not (Test-Path (Join-Path $AppDir 'kana.json'))) {
    Stop-With 'Falta kana.json: el repo está incompleto.'
}

function Resolve-Python {
    $candidates = @(
        @{ Exe = 'py';      Prefix = @('-3') },
        @{ Exe = 'python';  Prefix = @() },
        @{ Exe = 'python3'; Prefix = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -ErrorAction SilentlyContinue)) { continue }
        $out = & $c.Exe @($c.Prefix + @('-c', 'import sys; print(sys.executable)')) 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return ($out | Select-Object -First 1).Trim() }
    }
    return $null
}

$SystemPython = Resolve-Python
if (-not $SystemPython) {
    Stop-With "No encontré Python. Instalalo desde https://www.python.org/downloads/ o con 'winget install Python.Python.3.12', y tildá 'Add python.exe to PATH'."
}

& $SystemPython -c "import sys; sys.exit(0 if sys.version_info >= (3, $MinMinor) else 1)"
$tooOld = ($LASTEXITCODE -ne 0)
$ver = & $SystemPython -c 'import sys; print("%d.%d" % sys.version_info[:2])'
if ($tooOld) {
    Stop-With "Python $ver es muy viejo; hace falta 3.$MinMinor o más."
}
Write-Ok "Python $ver ($SystemPython)"

function Test-PyQt($exe) {
    & $exe -c 'import PyQt6.QtWidgets' 2>$null
    return ($LASTEXITCODE -eq 0)
}

# --------------------------------------------------------------------------- #
# Intérprete: sistema si ya tiene PyQt6, venv si no
# --------------------------------------------------------------------------- #
$Python = $null
$UseVenv = [bool]$Venv

if ($System) {
    if (-not (Test-PyQt $SystemPython)) {
        Stop-With "PyQt6 no está en ese Python. Instalalo con '$SystemPython -m pip install PyQt6' o corré .\install.ps1 -Venv"
    }
    $Python = $SystemPython
    Write-Ok 'uso el Python del sistema (ya tiene PyQt6)'
} elseif (-not $UseVenv) {
    if (Test-PyQt $SystemPython) {
        $Python = $SystemPython
        Write-Ok 'PyQt6 ya está en el Python del sistema, no hace falta entorno virtual'
    } else {
        $UseVenv = $true
    }
}

if ($UseVenv -and -not $Python) {
    $VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
    if (-not (Test-Path $VenvPython)) {
        Write-Step 'creando entorno virtual en .venv\ ...'
        & $SystemPython -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) { Stop-With 'No pude crear el entorno virtual.' }
    }
    if (-not (Test-PyQt $VenvPython)) {
        Write-Step 'instalando PyQt6 (puede tardar un rato, son ~70 MB) ...'
        & $VenvPython -m pip install --quiet --upgrade pip
        & $VenvPython -m pip install --quiet -r (Join-Path $AppDir 'requirements.txt')
        if ($LASTEXITCODE -ne 0) { Stop-With 'Falló la instalación de PyQt6. Mirá el error de pip más arriba.' }
    }
    if (-not (Test-PyQt $VenvPython)) { Stop-With 'PyQt6 quedó instalado pero no se puede importar.' }
    $Python = $VenvPython
    Write-Ok 'PyQt6 listo en .venv\'
}

# pythonw.exe corre la app sin ventana de consola
$Pythonw = Join-Path (Split-Path $Python -Parent) 'pythonw.exe'
if (-not (Test-Path $Pythonw)) {
    $Pythonw = $Python
    Write-Warn 'no encontré pythonw.exe; la app va a abrir una ventana de consola.'
}

# --------------------------------------------------------------------------- #
# Tabla de kana, ícono y acceso directo
# --------------------------------------------------------------------------- #
if (-not (Test-Path $TablePath)) {
    & $Python $Script --tabla | Out-Null
}

& $Python $Script --ico $IcoPath | Out-Null
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $IcoPath)) {
    Write-Warn 'no pude generar el ícono; el acceso directo va a usar el de Python.'
    $IcoPath = $null
} else {
    Write-Ok 'ícono generado (kana-tray.ico)'
}

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($Shortcut)
$lnk.TargetPath = $Pythonw
$lnk.Arguments = '"' + $Script + '"'
$lnk.WorkingDirectory = $AppDir
$lnk.Description = 'Practicá hiragana y katakana desde la bandeja del sistema'
if ($IcoPath) { $lnk.IconLocation = $IcoPath }
$lnk.Save()
Write-Ok "acceso directo en el menú Inicio ($Shortcut)"

if ($Autostart) {
    $cmd = '"' + $Pythonw + '" "' + $Script + '"'
    Set-ItemProperty -Path $RunKey -Name $RunName -Value $cmd
    Write-Ok 'arranca con la sesión (clave Run del usuario)'
}

# --------------------------------------------------------------------------- #
# Final
# --------------------------------------------------------------------------- #
Write-Host ''
Write-Step 'Listo. Buscá "Kana Tray" en el menú Inicio.'
if (-not $Autostart) {
    Write-Step 'Para que arranque solo: menú del ícono -> «Iniciar con la computadora»'
}
Write-Host ''
