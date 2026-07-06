param(
    [switch]$NoPrompt
)

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = Join-Path $projectDir 'start.bat'

if (-not (Test-Path -LiteralPath $startScript)) {
    Write-Host '[ERROR] No se encontro start.bat.' -ForegroundColor Red
    if (-not $NoPrompt) { Read-Host 'Pulsa Enter para cerrar' | Out-Null }
    exit 1
}

try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop 'NOVA DECK.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $startScript
    $shortcut.Arguments = '--browser'
    $shortcut.WorkingDirectory = $projectDir
    $shortcut.Description = 'Iniciar NOVA DECK y abrir el panel local'
    $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,14"
    $shortcut.WindowStyle = 1
    $shortcut.Save()

    Write-Host "[OK] Acceso directo creado: $shortcutPath" -ForegroundColor Green
    Write-Host 'Al abrirlo se iniciara el servidor y el navegador del PC.'
    if (-not $NoPrompt) { Read-Host 'Pulsa Enter para cerrar' | Out-Null }
    exit 0
}
catch {
    Write-Host "[ERROR] No se pudo crear el acceso directo: $($_.Exception.Message)" -ForegroundColor Red
    if (-not $NoPrompt) { Read-Host 'Pulsa Enter para cerrar' | Out-Null }
    exit 1
}
