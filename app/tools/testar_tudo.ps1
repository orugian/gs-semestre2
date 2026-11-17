# Roda a regressão de todos os componentes, em ordem, e resume o resultado.
# Uso (raiz do repositório):  powershell -NoProfile -ExecutionPolicy Bypass -File app\tools\testar_tudo.ps1 [-ComE2E] [-SemML]
# Pré-requisitos: uv, pnpm, Docker com o profile "teste" de pé, app/.env preenchido (ver README.md).
param([switch]$ComE2E, [switch]$SemML)
$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $PSScriptRoot 'ambiente_teste.ps1') | Out-Null
$resultado = [ordered]@{}
$componentes = @('api', 'cloud', 'tools')
if (-not $SemML) { $componentes += 'ml' }
foreach ($c in $componentes) {
  Push-Location (Join-Path $raiz "app\$c")
  uv sync --quiet
  uv run pytest -q
  $resultado["python:$c"] = $LASTEXITCODE
  Pop-Location
}
Push-Location (Join-Path $raiz 'app\web')
pnpm install --frozen-lockfile
pnpm run typecheck; $resultado['web:typecheck'] = $LASTEXITCODE
pnpm run test; $resultado['web:vitest'] = $LASTEXITCODE
pnpm run build; $resultado['web:build'] = $LASTEXITCODE
if ($ComE2E) {
  # O E2E precisa da API de teste em 127.0.0.1:8000 (ver README.md, "Rodar a aplicação").
  pnpm exec playwright test; $resultado['web:e2e'] = $LASTEXITCODE
}
Pop-Location
''
'== Resumo (0 = ok) =='
$resultado.GetEnumerator() | ForEach-Object { '{0,-16} {1}' -f $_.Key, $_.Value }
if ($resultado.Values | Where-Object { $_ -ne 0 }) { exit 1 }
