# Cria a persona fictícia "Marina" nos bancos de TESTE e percorre a jornada inteira pela API
# (consentimentos, intenção, currículo, competências, comparação, plano, exercício e laboratório).
# Precisa da aplicação no ar COM IA:  gravacao\subir_app.ps1 -ComIA
# Uso, na raiz do repositório:
#   powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\criar_conta_demo.ps1
# A senha é gerada aqui, salva FORA do repositório (pasta do usuário) e exibida só neste terminal.
# Não grave a tela deste terminal no vídeo. Faz ~2 chamadas pagas de IA (centavos).
. "$PSScriptRoot\_comum.ps1"
Set-Location $script:Raiz

try { $h = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 5 } catch { $h = $null }
if (-not $h -or $h.status -ne 'ok') { Falhar 'A API não está no ar. Rode antes: gravacao\subir_app.ps1 -ComIA' }

$pasta = Join-Path $env:LOCALAPPDATA 'CitizenTech'
New-Item -ItemType Directory -Force $pasta | Out-Null
$arq = Join-Path $pasta 'demo\persona_demo.json'
if (Test-Path $arq) {
  Escrever-Aviso 'Já existe uma persona criada neste computador; a jornada será repetida sobre ela.'
}

# Mesmas variáveis Oracle da API (schema de teste), para marcar a conta como "persona de demonstração".
. (Join-Path $script:App 'tools\ambiente_teste.ps1') | Out-Null
Escrever-Passo 'Criando a persona e percorrendo a jornada (1–3 min; usa a IA)'
Push-Location (Join-Path $script:App 'tools')
uv run --frozen --with oracledb python criar_persona_demo.py --base http://127.0.0.1:8000 --dados $pasta
$e = $LASTEXITCODE
Pop-Location
if ($e -ne 0) { Falhar 'A jornada falhou. Confira se a API foi aberta com -ComIA e veja a mensagem acima.' }

$cred = Get-Content -Raw -Encoding utf8 $arq | ConvertFrom-Json
Write-Host ''
Write-Host 'Entre em http://localhost:5173 > Minha transição com:' -ForegroundColor Green
Write-Host "  e-mail: $($cred.email)"
Write-Host "  senha:  $($cred.senha)"
Write-Host "(guardado em $arq; não mostre este terminal no vídeo)" -ForegroundColor Yellow
