# PlayWave - Script de Instalacao Windows
# Execute como Administrador

param(
    [string]$TargetFolder = "C:\Program Files\PlayWave"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PlayWave - Instalacao Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se esta rodando como Administrador
$isAdmin = [System.Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains `
    [System.Security.Principal.SecurityIdentifier]'S-1-5-32-544'

if (-not $isAdmin) {
    Write-Host "ERRO: Este script precisa rodar como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botao direito e selecione 'Executar como administrador'" -ForegroundColor Yellow
    exit 1
}

# Passo 1: Verificar Node.js
Write-Host "[1/4] Verificando Node.js..." -ForegroundColor Yellow
$nodeVersion = npm -v 2>$null
if (-not $nodeVersion) {
    Write-Host "ERRO: Node.js nao encontrado. Baixe em: https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Node.js encontrado (npm $nodeVersion)" -ForegroundColor Green
Write-Host ""

# Passo 2: Build do frontend
Write-Host "[2/4] Construindo aplicativo..." -ForegroundColor Yellow
Set-Location "frontend\electron"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Instalacao de dependencias falhou" -ForegroundColor Red
    exit 1
}
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Build falhou" -ForegroundColor Red
    exit 1
}
npm run electron:build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Build do Electron falhou" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Build concluido" -ForegroundColor Green
Write-Host ""

# Passo 3: Criar pasta de instalacao
Write-Host "[3/4] Instalando arquivos..." -ForegroundColor Yellow
if (-not (Test-Path $TargetFolder)) {
    New-Item -ItemType Directory -Path $TargetFolder -Force | Out-Null
}

# Copiar executavel
$exeFile = Get-ChildItem "dist-electron\*.exe" | Select-Object -First 1
if (-not $exeFile) {
    Write-Host "ERRO: Arquivo .exe nao encontrado em dist-electron\" -ForegroundColor Red
    exit 1
}

Copy-Item $exeFile.FullName "$TargetFolder\PlayWave.exe" -Force
Write-Host "OK - Instalado em $TargetFolder" -ForegroundColor Green
Write-Host ""

# Passo 4: Criar atalho no Menu Iniciar
Write-Host "[4/4] Criando atalho no Menu Iniciar..." -ForegroundColor Yellow
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$shortcutPath = "$startMenuPath\PlayWave.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "$TargetFolder\PlayWave.exe"
$shortcut.WorkingDirectory = $TargetFolder
$shortcut.Description = "PlayWave Player"
$shortcut.Save()
Write-Host "OK - Atalho criado" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalacao Concluida!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "1. Procure 'PlayWave' no Menu Iniciar"
Write-Host "2. Clique com botao direito -> Propriedades"
Write-Host "3. Clique em 'Avancado' -> marque 'Executar como administrador'"
Write-Host "4. Clique OK e execute"
Write-Host ""
Write-Host "Para mais informacoes, veja INSTALACAO_E_USO.md" -ForegroundColor Cyan
