# Abre a aplicação para gravar: API em 127.0.0.1:8000 e site em http://localhost:5173.
# Rode na raiz do repositório, depois de gravacao\preparar.ps1:
#   powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1 [-ComIA]
# Usa só os bancos de TESTE e uma pasta temporária nova para leituras. Nunca envia nada à AWS.
# -ComIA lê OPENROUTER_API_KEY do app\.env de quem roda (chamadas pagas, centavos cada) para que a
#        extração de competências e a correção da resposta aberta funcionem. Sem ela, essas duas
#        etapas mostram "serviço indisponível"; o resto da aplicação funciona normalmente.
# Para encerrar: feche as duas janelas que este script abre (API e site).
param([switch]$ComIA)
. "$PSScriptRoot\_comum.ps1"
Set-Location $script:Raiz

if (-not (Test-Path $script:ArquivoEnv)) { Falhar 'app\.env não existe. Rode antes: gravacao\preparar.ps1' }
foreach ($p in 8000, 5173) { if (Testar-Porta $p) { Falhar "A porta $p já está em uso. Feche o programa que a usa (ou uma janela antiga deste script)." } }

$chaveIA = ''
if ($ComIA) {
  $chaveIA = (Ler-Env)['OPENROUTER_API_KEY']
  if (-not $chaveIA) { Falhar '-ComIA pedido, mas app\.env não tem OPENROUTER_API_KEY. Peça a chave a quem administra o projeto.' }
}

# Script da janela da API: carrega o ambiente de teste (bancos locais, segredos efêmeros, runtime
# novo, integrações externas desligadas) e só então, se pedido, a chave de IA.
$api = Join-Path $env:TEMP ("citizentech_api_" + [guid]::NewGuid().ToString('N') + '.ps1')
$linhasIA = ''
if ($ComIA) {
  $linhasIA = @"
`$v = @{}; foreach (`$l in Get-Content -Encoding utf8 '$($script:ArquivoEnv)') { if (`$l -match '^\s*(OPENROUTER_[A-Z_]+)\s*=\s*(.*)$') { `$x = `$Matches[2]; if (`$x -match '^\s*"([^"]*)"') { `$x = `$Matches[1] } else { `$x = (`$x -replace '(?:\s+#|^#).*$','').Trim() }; Set-Item "env:`$(`$Matches[1])" `$x } }
"@
}
$conteudo = @"
`$Host.UI.RawUI.WindowTitle = 'CitizenTech - API (feche para encerrar)'
Set-Location '$($script:Raiz)'
. .\app\tools\ambiente_teste.ps1 | Out-Null
$linhasIA
Set-Location app\api
Write-Host 'API CitizenTech em http://127.0.0.1:8000  (bancos de teste; sem AWS)' -ForegroundColor Cyan
uv run --frozen uvicorn citizentech.main:app --host 127.0.0.1 --port 8000
"@
[IO.File]::WriteAllText($api, $conteudo, (New-Object Text.UTF8Encoding $true))

Escrever-Passo 'Subindo a API'
Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-File', $api | Out-Null
if (-not (Esperar-Url 'http://127.0.0.1:8000/health' 90)) { Falhar 'A API não respondeu em 90 s. Veja a janela "CitizenTech - API".' }
Escrever-Ok 'API no ar'
$m = try { (Invoke-WebRequest 'http://127.0.0.1:8000/mercado/analista_dados_bi?uf=SP' -UseBasicParsing -TimeoutSec 10).StatusCode } catch { $_.Exception.Response.StatusCode.value__ }
if ($m -eq 200) { Escrever-Ok 'dados de mercado carregados' } else { Escrever-Aviso "Mercado respondeu HTTP $m (as telas Mercado e Painel técnico podem mostrar erro)" }
if ($ComIA) { Escrever-Ok 'IA ligada (OpenRouter)' } else { Escrever-Aviso 'IA desligada: extração de competências e correção da resposta aberta ficam indisponíveis' }

Escrever-Passo 'Subindo o site'
$web = Join-Path $script:App 'web'
Start-Process powershell -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-NoExit', '-Command', "`$Host.UI.RawUI.WindowTitle='CitizenTech - site (feche para encerrar)'; Set-Location '$web'; pnpm run dev" | Out-Null
if (-not (Esperar-Url 'http://localhost:5173' 90)) { Falhar 'O site não respondeu em 90 s. Veja a janela "CitizenTech - site".' }
Escrever-Ok 'site no ar'

Start-Process 'http://localhost:5173'
Write-Host ''
Write-Host 'Aplicação aberta em http://localhost:5173' -ForegroundColor Green
Write-Host 'Conta para o vídeo:  powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\criar_conta_demo.ps1' -ForegroundColor Green
