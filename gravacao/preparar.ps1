# Prepara este computador para gravar os vídeos do CitizenTech. Rode UMA vez, na raiz do repositório:
#   powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\preparar.ps1
# O que faz: confere ferramentas; cria app\.env com senhas locais aleatórias (só se ainda não existir);
# sobe os bancos de TESTE no Docker; cria o schema de teste e as tabelas; instala dependências.
# Não usa nuvem nem serviços pagos e nunca mostra senhas.
param([switch]$SemInstalar)
. "$PSScriptRoot\_comum.ps1"
Set-Location $script:Raiz

Escrever-Passo '1/6  Ferramentas'
Exigir-Comando 'uv' 'Instale: https://docs.astral.sh/uv/  (powershell -c "irm https://astral.sh/uv/install.ps1 | iex")'
Exigir-Comando 'pnpm' 'Instale Node.js 24 e depois: npm install -g pnpm'
Exigir-Comando 'docker' 'Instale o Docker Desktop e abra-o antes de continuar.'
docker info *> $null
if ($LASTEXITCODE -ne 0) { Falhar 'O Docker Desktop está instalado mas parado. Abra-o, espere ficar verde e rode de novo.' }
Escrever-Ok 'Docker ativo'

Escrever-Passo '2/6  Arquivo app\.env'
if (Test-Path $script:ArquivoEnv) {
  Escrever-Ok 'app\.env já existe: mantido como está (nada foi sobrescrito)'
} else {
  function Gerar([int]$n = 24) {
    $b = New-Object byte[] $n; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    # Só letras e dígitos: o Oracle e a URL do Mongo não aceitam bem símbolos.
    (([Convert]::ToBase64String($b)) -replace '[^A-Za-z0-9]', '').Substring(0, [Math]::Min(20, $n))
  }
  $texto = Get-Content -Raw -Encoding utf8 (Join-Path $script:App '.env.example')
  $gerados = @{
    'ORACLE_PASSWORD' = 'Ct' + (Gerar); 'ORACLE_ADMIN_PASSWORD' = 'Ct' + (Gerar)
    'ORACLE_TESTE_PASSWORD' = 'Ct' + (Gerar); 'POSTGRES_TESTE_PASSWORD' = (Gerar)
    'MONGO_TESTE_PASSWORD' = (Gerar); 'JWT_SECRET' = (Gerar 48) + (Gerar 48); 'DEVICE_KEY' = (Gerar 32)
  }
  foreach ($k in $gerados.Keys) {
    $texto = [regex]::Replace($texto, "(?m)^$k=[^\r\n#]*", "$k=$($gerados[$k])   ")
  }
  $texto = [regex]::Replace($texto, '(?m)^CITIZENTECH_DADOS=[^\r\n]*', 'CITIZENTECH_DADOS=')
  [IO.File]::WriteAllText($script:ArquivoEnv, $texto, (New-Object Text.UTF8Encoding $false))
  Escrever-Ok 'app\.env criado com senhas locais aleatórias (não aparecem na tela)'
}
$env_ = Ler-Env
foreach ($k in 'ORACLE_PASSWORD', 'ORACLE_ADMIN_PASSWORD', 'ORACLE_TESTE_PASSWORD', 'POSTGRES_TESTE_PASSWORD', 'MONGO_TESTE_PASSWORD') {
  if (-not $env_[$k]) { Falhar "app\.env sem valor para $k. Preencha (qualquer senha local) e rode de novo." }
}
if ($env_['ORACLE_TESTE_USER'] -notmatch '^CT_.*TESTE') { Falhar 'ORACLE_TESTE_USER em app\.env precisa começar com CT_ e conter TESTE (ex.: CT_TESTE_S9).' }

Escrever-Passo '3/6  Bancos de teste no Docker (a primeira vez baixa ~3 GB e leva alguns minutos)'
docker compose -f app\docker-compose.yml --profile teste up -d --wait
if ($LASTEXITCODE -ne 0) { Falhar 'Os bancos não subiram. Veja: docker compose -f app\docker-compose.yml --profile teste logs' }
Escrever-Ok 'Oracle, PostgreSQL e MongoDB de teste no ar (só em 127.0.0.1)'

Escrever-Passo '4/6  Schema Oracle de teste'
$usuario = $env_['ORACLE_TESTE_USER']
$sql = @"
WHENEVER SQLERROR CONTINUE
SET FEEDBACK OFF
DECLARE n NUMBER; BEGIN
  SELECT COUNT(*) INTO n FROM all_users WHERE username = UPPER('$usuario');
  IF n = 0 THEN
    EXECUTE IMMEDIATE 'CREATE USER $usuario IDENTIFIED BY "' || '$($env_['ORACLE_TESTE_PASSWORD'])' || '" QUOTA UNLIMITED ON USERS';
  END IF;
  EXECUTE IMMEDIATE 'GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO $usuario';
END;
/
EXIT
"@
$sql | docker exec -i citizentech-oracle-1 bash -c 'sqlplus -L -s system/"$ORACLE_PASSWORD"@localhost:1521/FREEPDB1' | Out-Null
if ($LASTEXITCODE -ne 0) { Falhar 'Não foi possível criar o schema de teste no Oracle.' }
Escrever-Ok "schema $usuario pronto"

Escrever-Passo '5/6  Dependências'
if ($SemInstalar) { Escrever-Aviso 'pulado (-SemInstalar)' } else {
  foreach ($c in 'api', 'tools', 'cloud') {
    Push-Location (Join-Path $script:App $c); uv sync --frozen --quiet; $e = $LASTEXITCODE; Pop-Location
    if ($e -ne 0) { Falhar "uv sync falhou em app\$c" }
    Escrever-Ok "app\$c"
  }
  Push-Location (Join-Path $script:App 'web'); pnpm install --frozen-lockfile --silent; $e = $LASTEXITCODE; Pop-Location
  if ($e -ne 0) { Falhar 'pnpm install falhou em app\web' }
  Escrever-Ok 'app\web'
}

Escrever-Passo '6/6  Tabelas no schema de teste'
. (Join-Path $script:App 'tools\ambiente_teste.ps1') | Out-Null
Push-Location (Join-Path $script:App 'tools')
uv run --frozen --with oracledb python aplicar_ddl.py --confirmar | Select-Object -Last 2
$e = $LASTEXITCODE
if ($e -eq 0) { uv run --frozen --with oracledb --with pyyaml python carregar_catalogo_oracle.py --confirmar | Select-Object -Last 1; $e = $LASTEXITCODE }
Pop-Location
if ($e -ne 0) { Falhar 'Falha ao criar as tabelas ou carregar o catálogo no Oracle de teste.' }
Escrever-Ok 'tabelas e catálogo prontos'

Write-Host ''
Write-Host 'Pronto. Próximo passo:  powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1' -ForegroundColor Green
