# Demonstração Cloud SEM AWS: emulador local da Function URL (mesmo código da Lambda) gravando no
# PostgreSQL de teste. Mostra o fluxo "simulador envia -> log recebe -> banco grava".
# Use quando não houver Learner Lab ativo. No vídeo, diga que esta parte é o EMULADOR LOCAL e use as
# capturas em 06_Cloud\evidencias\ para a execução real na AWS.
# Rode na raiz do repositório, depois de gravacao\preparar.ps1:
#   powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\cloud_local.ps1
# Abre uma janela com o log do emulador (porta 8099). Neste terminal, roda o simulador, os testes
# negativos e a consulta ao banco, com pausas para você narrar.
. "$PSScriptRoot\_comum.ps1"
Set-Location $script:Raiz
if (Testar-Porta 8099) { Falhar 'A porta 8099 já está em uso (emulador aberto?). Feche a janela antiga.' }

. (Join-Path $script:App 'tools\ambiente_teste.ps1') | Out-Null
if (-not $env:PG_TESTE_PASSWORD) { Falhar 'Sem senha do PostgreSQL de teste. Rode gravacao\preparar.ps1.' }

Escrever-Passo 'Tabela de ocorrências no PostgreSQL de teste'
$ddl = (Get-Content -Raw -Encoding utf8 (Join-Path $script:App 'cloud\sql\ocorrencias.sql')) -split '-- FIM_DDL' | Select-Object -First 1
$ddl | docker exec -i citizentech-postgres-1 psql -q -U citizentech_teste -d citizentech_teste -v ON_ERROR_STOP=1 | Out-Null
if ($LASTEXITCODE -ne 0) { Falhar 'Não foi possível criar a tabela ocorrencias.' }
Escrever-Ok 'tabela pronta'

# Variáveis só deste processo e da janela do emulador (nada vai para a AWS).
$env:DB_HOST = $env:PG_TESTE_HOST; $env:DB_PORT = $env:PG_TESTE_PORT; $env:DB_NAME = $env:PG_TESTE_DB
$env:DB_USER = $env:PG_TESTE_USER; $env:DB_PASSWORD = $env:PG_TESTE_PASSWORD; $env:DB_SSLMODE = 'disable'
$env:SENTIMENTO_PROVEDOR = 'desligado'
Remove-Item env:FUNCTION_URL -ErrorAction SilentlyContinue

Escrever-Passo 'Abrindo o emulador (janela "CitizenTech - log da Lambda local")'
$cloud = Join-Path $script:App 'cloud'
Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-Command', "`$Host.UI.RawUI.WindowTitle='CitizenTech - log da Lambda local'; Set-Location '$cloud'; uv run --frozen python -m citizentech_cloud.servidor_local --porta 8099" | Out-Null
if (-not (Esperar-Url 'http://127.0.0.1:8099/health' 60)) { Falhar 'O emulador não respondeu.' }
Escrever-Ok 'emulador no ar em http://127.0.0.1:8099'

$url = 'http://127.0.0.1:8099'
Push-Location $cloud
try {
  Escrever-Passo 'Health'
  curl.exe -s "$url/health"; Write-Host ''
  Read-Host 'ENTER para enviar o cenário normal (sem chave)'
  uv run --frozen python -m citizentech_cloud.simulador --url $url --cenario normal --leituras 2 --intervalo 1
  Read-Host 'ENTER para a evolução 30 -> 50 °C com chave (normal -> atenção -> crítico)'
  uv run --frozen python -m citizentech_cloud.simulador --url $url --cenario evolucao --leituras 6 --intervalo 1 --com-chave
  Read-Host 'ENTER para os testes negativos (sem "valor" -> 400; chave errada -> 401)'
  $corpo = '{"dispositivo_id":"lab-iot-bancada-01","metrica":"temperatura_c","unidade":"C","medido_em":"2026-11-18T12:00:00Z"}'
  $tmp = New-TemporaryFile; [IO.File]::WriteAllText($tmp, $corpo)
  Write-Host 'Leitura sem "valor":'; curl.exe -s -o NUL -w "HTTP %{http_code}`n" -H 'Content-Type: application/json' --data-binary "@$tmp" "$url/ocorrencias"
  $corpo2 = '{"dispositivo_id":"lab-iot-bancada-01","metrica":"temperatura_c","unidade":"C","valor":30,"medido_em":"2026-11-18T12:00:00Z"}'
  [IO.File]::WriteAllText($tmp, $corpo2)
  # Chave aleatória gerada agora: de propósito, nunca é a chave verdadeira do dispositivo.
  $errada = [guid]::NewGuid().ToString('N')
  Write-Host 'Chave errada:'; curl.exe -s -o NUL -w "HTTP %{http_code}`n" -H 'Content-Type: application/json' -H "X-Device-Key: $errada" --data-binary "@$tmp" "$url/ocorrencias"
  Remove-Item $tmp
  Read-Host 'ENTER para consultar o banco'
  $q = 'SELECT id, dispositivo_id, metrica, valor, nivel_risco, alerta, autenticado, analise_status, criado_em FROM ocorrencias ORDER BY id DESC LIMIT 10;'
  $q | docker exec -i citizentech-postgres-1 psql -U citizentech_teste -d citizentech_teste
  Write-Host 'Mesma consulta pela API:'; curl.exe -s "$url/ocorrencias?limite=5"; Write-Host ''
} finally { Pop-Location }
Write-Host ''
Write-Host 'Fim. Feche a janela do emulador para encerrar.' -ForegroundColor Green
