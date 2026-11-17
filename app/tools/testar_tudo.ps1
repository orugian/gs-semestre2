# Roda a regressão de todos os componentes, em ordem, e resume o resultado.
# Uso (raiz do repositório):  powershell -NoProfile -ExecutionPolicy Bypass -File app\tools\testar_tudo.ps1 [-ComE2E] [-SemML]
# Pré-requisitos: uv, pnpm, Docker com o profile "teste" de pé, app/.env preenchido (ver README.md).
param([switch]$ComE2E, [switch]$SemML)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Não preservar BANCOS_TESTE_FALTANDO de fora
Remove-Item -Path 'env:BANCOS_TESTE_FALTANDO' -ErrorAction SilentlyContinue

# Validar ferramentas essenciais antes de iniciar qualquer execução
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv não encontrado no PATH."
    exit 1
}
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Error "pnpm não encontrado no PATH."
    exit 1
}

try {
    . (Join-Path $PSScriptRoot 'ambiente_teste.ps1') | Out-Null
} catch {
    Write-Error $_
    exit 1
}

if ($env:BANCOS_TESTE_FALTANDO) {
    Write-Error ("Runner completo bloqueado: faltam configurações de banco de teste ({0}). Preencha app/.env." -f $env:BANCOS_TESTE_FALTANDO)
    exit 1
}

$resultado = [ordered]@{}
$componentes = @('api', 'cloud', 'tools')
if (-not $SemML) { $componentes += 'ml' }

foreach ($c in $componentes) {
    Push-Location (Join-Path $raiz "app\$c")
    try {
        $global:LASTEXITCODE = $null
        uv sync --frozen --quiet
        $exitSync = $LASTEXITCODE
        if ($null -eq $exitSync -or $exitSync -ne 0) {
            $resultado["python:$c"] = if ($null -ne $exitSync) { $exitSync } else { 1 }
            Write-Error ("uv sync falhou no componente python:{0} com codigo {1}" -f $c, $resultado["python:$c"])
            exit 1
        }

        $global:LASTEXITCODE = $null
        uv run --frozen pytest -q
        $exitTest = $LASTEXITCODE
        $resultado["python:$c"] = if ($null -ne $exitTest) { $exitTest } else { 1 }
        if ($resultado["python:$c"] -ne 0) {
            Write-Error ("pytest falhou no componente python:{0} com codigo {1}" -f $c, $resultado["python:$c"])
            exit 1
        }
    } finally {
        Pop-Location
    }
}

Push-Location (Join-Path $raiz 'app\web')
try {
    $global:LASTEXITCODE = $null
    pnpm install --frozen-lockfile
    $exitInstall = $LASTEXITCODE
    if ($null -eq $exitInstall -or $exitInstall -ne 0) {
        $resultado['web:install'] = if ($null -ne $exitInstall) { $exitInstall } else { 1 }
        Write-Error ("pnpm install falhou com codigo {0}" -f $resultado['web:install'])
        exit 1
    }

    $global:LASTEXITCODE = $null
    pnpm run typecheck
    $resultado['web:typecheck'] = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 1 }
    if ($resultado['web:typecheck'] -ne 0) { exit 1 }

    $global:LASTEXITCODE = $null
    pnpm run test
    $resultado['web:vitest'] = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 1 }
    if ($resultado['web:vitest'] -ne 0) { exit 1 }

    $global:LASTEXITCODE = $null
    pnpm run build
    $resultado['web:build'] = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 1 }
    if ($resultado['web:build'] -ne 0) { exit 1 }

    if ($ComE2E) {
        # O E2E precisa da API de teste em 127.0.0.1:8000 (ver README.md, "Rodar a aplicação").
        $global:LASTEXITCODE = $null
        pnpm exec playwright test
        $resultado['web:e2e'] = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 1 }
        if ($resultado['web:e2e'] -ne 0) { exit 1 }
    }
} finally {
    Pop-Location
}

''
'== Resumo (0 = ok) =='
$resultado.GetEnumerator() | ForEach-Object { '{0,-16} {1}' -f $_.Key, $_.Value }
if ($resultado.Values | Where-Object { $_ -ne 0 }) { exit 1 }
