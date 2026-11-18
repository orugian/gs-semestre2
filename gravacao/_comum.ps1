# Funções compartilhadas pelos scripts de gravação. Carregar com:  . "$PSScriptRoot\_comum.ps1"
# Nunca imprime senhas ou chaves.

$script:Raiz = Split-Path -Parent $PSScriptRoot
$script:App = Join-Path $script:Raiz 'app'
$script:ArquivoEnv = Join-Path $script:App '.env'

function Escrever-Passo([string]$texto) { Write-Host ''; Write-Host "==> $texto" -ForegroundColor Cyan }
function Escrever-Ok([string]$texto) { Write-Host "    ok  $texto" -ForegroundColor Green }
function Escrever-Aviso([string]$texto) { Write-Host "    !!  $texto" -ForegroundColor Yellow }
function Falhar([string]$texto) { Write-Host "    XX  $texto" -ForegroundColor Red; exit 1 }

function Ler-Env {
  # Lê app/.env sem expor valores. Trata aspas e comentários no fim da linha.
  $v = @{}
  if (-not (Test-Path $script:ArquivoEnv)) { return $v }
  foreach ($linha in Get-Content -Encoding utf8 $script:ArquivoEnv) {
    if ($linha -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
      $chave = $Matches[1]; $bruto = $Matches[2]
      if ($bruto -match '^\s*"([^"]*)"') { $valor = $Matches[1] }
      elseif ($bruto -match "^\s*'([^']*)'") { $valor = $Matches[1] }
      else { $valor = ($bruto -replace '(?:\s+#|^#).*$', '').Trim() }
      $v[$chave] = $valor
    }
  }
  return $v
}

function Exigir-Comando([string]$nome, [string]$como) {
  if (-not (Get-Command $nome -ErrorAction SilentlyContinue)) { Falhar "$nome não encontrado. $como" }
  Escrever-Ok "$nome encontrado"
}

function Testar-Porta([int]$porta) {
  return [bool](Get-NetTCPConnection -LocalPort $porta -State Listen -ErrorAction SilentlyContinue)
}

function Esperar-Url([string]$url, [int]$segundos = 60) {
  $fim = (Get-Date).AddSeconds($segundos)
  while ((Get-Date) -lt $fim) {
    try { $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -lt 500) { return $true } } catch {}
    Start-Sleep -Milliseconds 700
  }
  return $false
}
