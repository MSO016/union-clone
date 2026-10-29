<#
.SYNOPSIS
    Prepara o ambiente do Union Manager (Windows).

.DESCRIPTION
    - Verifica/instala Python 3.11+ via winget (se necessário)
    - Cria o ambiente virtual (.venv)
    - Instala as dependências do requirements.txt via pip
    NÃO usa Scoop; apenas winget + pip.

.EXECUÇÃO
    Na pasta do projeto:
        powershell -ExecutionPolicy Bypass -File setup.ps1
#>
$ErrorActionPreference = "Stop"

$raiz = $PSScriptRoot
$venv = Join-Path $raiz ".venv"
$pythonVenv = Join-Path $venv "Scripts\python.exe"

function Encontrar-Python {
    # 3.11+ aceito; procura qualquer instalador disponível no PATH.
    foreach ($candidato in @("python", "py")) {
        $exe = Get-Command $candidato -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        $v = & $exe.Source -c "import sys; print(sys.version_info >= (3, 11))" 2>$null
        if ($v -eq "True") { return $exe.Source }
    }
    return $null
}

Write-Host "== Union Manager — setup ==" -ForegroundColor Cyan

# 1) Python
$python = Encontrar-Python
if (-not $python) {
    Write-Host "Python 3.11+ não encontrado. Tentando instalar via winget..." -ForegroundColor Yellow
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Error "winget não encontrado. Instale o Python manualmente: https://python.org/downloads"
        exit 1
    }
    winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements
    # O PATH só é atualizado em novas janelas; procura no local padrão.
    $python = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
    if (-not (Test-Path $python)) {
        Write-Error "Instalação do Python não encontrada após o winget. Reabra o terminal e rode o setup novamente."
        exit 1
    }
}
Write-Host "Python: $python"

# 2) Ambiente virtual
if (-not (Test-Path $pythonVenv)) {
    Write-Host "Criando ambiente virtual em $venv ..."
    & $python -m venv $venv
} else {
    Write-Host "Ambiente virtual já existe."
}

# 3) Dependências
Write-Host "Instalando dependências (requirements.txt)..."
& $pythonVenv -m pip install --upgrade pip | Out-Null
& $pythonVenv -m pip install -r (Join-Path $raiz "requirements.txt")

Write-Host ""
Write-Host "Setup concluído." -ForegroundColor Green
Write-Host "Para rodar o app:  $pythonVenv main.py"
Write-Host "Para rodar testes: $pythonVenv -m tests.test_dominio (e os demais tests.test_*)"
