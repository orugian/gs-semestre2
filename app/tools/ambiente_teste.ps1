# Carrega no processo atual as variáveis dos bancos de TESTE a partir de app/.env, sem imprimir valores.
# Uso (a partir da raiz do repositório):  . .\app\tools\ambiente_teste.ps1
# Exige os serviços de teste de pé:      docker compose -f app\docker-compose.yml --profile teste up -d --wait
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$arquivo = Join-Path $raiz 'app\.env'
if (-not (Test-Path $arquivo)) { throw "app/.env não encontrado: copie app/.env.example e preencha." }
$v = @{}
Get-Content -Encoding utf8 $arquivo | ForEach-Object {
  if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
    $chave = $Matches[1]; $valor = $Matches[2].Trim()
    if ($valor -match '^"([^"]*)"' -or $valor -match "^'([^']*)'") { $valor = $Matches[1] }
    else { $valor = ($valor -replace '\s+#.*$', '').Trim() }
    $v[$chave] = $valor
  }
}
# O Docker publica as portas só em IPv4; "localhost" tenta IPv6 primeiro e o Oracle espera ~20 s.
$env:ORACLE_DSN = ($v['ORACLE_DSN'] -replace '^localhost(?=[:/])', '127.0.0.1')
$env:ORACLE_USER = $v['ORACLE_TESTE_USER']
$env:ORACLE_PASSWORD = $v['ORACLE_TESTE_PASSWORD']
$env:MONGODB_URI = 'mongodb://citizentech_teste:' + [uri]::EscapeDataString([string]$v['MONGO_TESTE_PASSWORD']) + '@127.0.0.1:27018/?authSource=admin'
$env:MONGODB_DB = 'citizentech_teste'
$env:PG_TESTE_HOST = '127.0.0.1'
$env:PG_TESTE_PORT = '5433'
$env:PG_TESTE_DB = 'citizentech_teste'
$env:PG_TESTE_USER = 'citizentech_teste'
$env:PG_TESTE_PASSWORD = $v['POSTGRES_TESTE_PASSWORD']
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'
$faltando = 'ORACLE_USER', 'ORACLE_PASSWORD', 'PG_TESTE_PASSWORD' | Where-Object { -not (Get-Item "env:$_" -ErrorAction SilentlyContinue).Value }
if ($faltando) { Write-Warning ("Sem valor em app/.env para: {0}. Os testes que dependem deles serão pulados." -f ($faltando -join ', ')) }
"ambiente de teste carregado (valores não exibidos)"
