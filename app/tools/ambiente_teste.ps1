# Carrega no processo atual as variáveis dos bancos de TESTE a partir de app/.env, sem imprimir valores.
# Uso (a partir da raiz do repositório):  . .\app\tools\ambiente_teste.ps1
# Exige os serviços de teste de pé:      docker compose -f app\docker-compose.yml --profile teste up -d --wait

& {
    param()

    $raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $arquivo = Join-Path $raiz 'app\.env'
    if (-not (Test-Path $arquivo)) {
        throw "app/.env não encontrado: copie app/.env.example e preencha."
    }

    # Limpa variáveis de bancos faltando herdadas de fora
    Remove-Item -Path 'env:BANCOS_TESTE_FALTANDO' -ErrorAction SilentlyContinue

    # Remove credenciais de serviços pagos/nuvem, variáveis AWS_* e URLs externas
    Get-ChildItem env:AWS_* -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path "env:$($_.Name)" -ErrorAction SilentlyContinue
    }

    $removerHerdadas = @(
        'OPENROUTER_API_KEY', 'OPENROUTER_BASE_URL', 'OPENROUTER_MODEL',
        'OPENROUTER_MODEL_FALLBACK', 'OPENROUTER_DATA_COLLECTION',
        'HF_TOKEN', 'HF_MODEL', 'HF_API_URL',
        'ADZUNA_APP_ID', 'ADZUNA_APP_KEY',
        'FUNCTION_URL',
        'CITIZENTECH_ADZUNA_SNAPSHOT',
        'CITIZENTECH_MERCADO_SNAPSHOT',
        'DB_HOST', 'DB_PASSWORD', 'DB_USER', 'DB_NAME', 'DB_PORT', 'DB_SSLMODE', 'DB_SSLROOTCERT'
    )
    foreach ($varNome in $removerHerdadas) {
        Remove-Item -Path "env:$varNome" -ErrorAction SilentlyContinue
    }

    # Desabilita provedor de sentimento para não acionar serviços externos/pagos
    $env:SENTIMENTO_PROVEDOR = 'desligado'

    # Allowlist estrita de chaves de teste permitidas a partir de app/.env
    $chavesPermitidas = @(
        'ORACLE_DSN',
        'ORACLE_TESTE_USER',
        'ORACLE_TESTE_PASSWORD',
        'POSTGRES_TESTE_PASSWORD',
        'MONGO_TESTE_PASSWORD',
        'CITIZENTECH_MERCADO_SNAPSHOT'
    )

    $v = @{}
    Get-Content -Encoding utf8 $arquivo | ForEach-Object {
        $linha = $_
        if ($linha -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $chave = $Matches[1]
            if ($chavesPermitidas -contains $chave) {
                $raw = $Matches[2]
                if ($raw -match '^\s*"([^"]*)"(?:\s*#.*)?$') {
                    $valor = $Matches[1]
                } elseif ($raw -match "^\s*'([^']*)'(?:\s*#.*)?$") {
                    $valor = $Matches[1]
                } else {
                    $valor = ($raw -replace '(?:\s+#|^#).*$', '').Trim()
                }
                $v[$chave] = $valor
            }
        }
    }

    # Validação estrita do endpoint Oracle antes de atribuir credenciais:
    # Apenas loopback (127.0.0.1 ou localhost), porta 1521 e FREEPDB1 do compose local
    $oracleDsn = if ($v.ContainsKey('ORACLE_DSN') -and -not [string]::IsNullOrWhiteSpace($v['ORACLE_DSN'])) {
        $v['ORACLE_DSN'].Trim()
    } else {
        '127.0.0.1:1521/FREEPDB1'
    }
    # O Docker publica as portas só em IPv4; "localhost" tenta IPv6 primeiro e o Oracle espera ~20 s.
    $oracleDsn = $oracleDsn -replace '^localhost(?=[:/])', '127.0.0.1'
    if ($oracleDsn -notmatch '^127\.0\.0\.1:1521/FREEPDB1$') {
        throw "DSN externo não permitido para testes: apenas loopback 127.0.0.1:1521/FREEPDB1 do compose local."
    }

    # Validação de ORACLE_TESTE_USER: trava para evitar escrita em banco de aplicação (ex: citizentech)
    $oracleUser = if ($v.ContainsKey('ORACLE_TESTE_USER')) { $v['ORACLE_TESTE_USER'].Trim() } else { '' }
    if (-not [string]::IsNullOrWhiteSpace($oracleUser)) {
        if ($oracleUser -notmatch '^CT_.*TESTE.*$') {
            throw "ORACLE_TESTE_USER inválido ($oracleUser): deve começar com 'CT_' e conter 'TESTE' para evitar escrita em banco de aplicação."
        }
    }

    # Atribuição segura de variáveis Oracle
    $env:ORACLE_DSN = $oracleDsn
    $env:ORACLE_USER = $oracleUser
    $env:ORACLE_PASSWORD = if ($v.ContainsKey('ORACLE_TESTE_PASSWORD')) { $v['ORACLE_TESTE_PASSWORD'] } else { '' }

    # Mongo local
    $mongoPass = if ($v.ContainsKey('MONGO_TESTE_PASSWORD')) { $v['MONGO_TESTE_PASSWORD'] } else { '' }
    $env:MONGO_TESTE_PASSWORD = $mongoPass
    if (-not [string]::IsNullOrWhiteSpace($mongoPass)) {
        $env:MONGODB_URI = 'mongodb://citizentech_teste:' + [uri]::EscapeDataString([string]$mongoPass) + '@127.0.0.1:27018/?authSource=admin'
        $env:MONGODB_DB = 'citizentech_teste'
    } else {
        Remove-Item -Path 'env:MONGODB_URI' -ErrorAction SilentlyContinue
        Remove-Item -Path 'env:MONGODB_DB' -ErrorAction SilentlyContinue
    }

    # Postgres local
    $env:PG_TESTE_HOST = '127.0.0.1'
    $env:PG_TESTE_PORT = '5433'
    $env:PG_TESTE_DB = 'citizentech_teste'
    $env:PG_TESTE_USER = 'citizentech_teste'
    $env:PG_TESTE_PASSWORD = if ($v.ContainsKey('POSTGRES_TESTE_PASSWORD')) { $v['POSTGRES_TESTE_PASSWORD'] } else { '' }

    # Preservar snapshot local explicitamente informado para leitura de Mercado
    if ($v.ContainsKey('CITIZENTECH_MERCADO_SNAPSHOT') -and -not [string]::IsNullOrWhiteSpace($v['CITIZENTECH_MERCADO_SNAPSHOT'])) {
        $env:CITIZENTECH_MERCADO_SNAPSHOT = $v['CITIZENTECH_MERCADO_SNAPSHOT']
    }

    # Segredos efêmeros para processo de teste (>=32 caracteres)
    $env:JWT_SECRET = 'citizentech_test_jwt_secret_' + [System.Guid]::NewGuid().ToString('N')
    $env:DEVICE_KEY = 'citizentech_test_device_key_' + [System.Guid]::NewGuid().ToString('N')

    # Runtime temporário novo por chamada para outbox, leituras e dados privados
    $tmpBase = if ($env:CITIZENTECH_TMP -and (Test-Path $env:CITIZENTECH_TMP)) {
        $env:CITIZENTECH_TMP
    } else {
        [System.IO.Path]::GetTempPath()
    }
    $runtimeId = 'ct_test_rt_' + [System.Guid]::NewGuid().ToString('N')
    $runtimeDir = Join-Path $tmpBase $runtimeId
    [System.IO.Directory]::CreateDirectory($runtimeDir) | Out-Null
    $env:CITIZENTECH_DADOS = $runtimeDir
    $env:CITIZENTECH_LEITURAS_CSV = Join-Path $runtimeDir 'leituras.csv'
    $env:CITIZENTECH_OUTBOX_DB = Join-Path $runtimeDir 'outbox.db'

    # Encoding
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'

    # Identificar bancos faltando (sem imprimir segredos)
    $faltando = @('ORACLE_USER', 'ORACLE_PASSWORD', 'PG_TESTE_PASSWORD', 'MONGO_TESTE_PASSWORD') | Where-Object {
        -not (Get-Item "env:$_" -ErrorAction SilentlyContinue).Value
    }
    if ($faltando) {
        $env:BANCOS_TESTE_FALTANDO = ($faltando -join ', ')
        Write-Warning ("Sem valor em app/.env para: {0}. Os testes que dependem deles serão pulados." -f ($faltando -join ', '))
    } else {
        Remove-Item -Path 'env:BANCOS_TESTE_FALTANDO' -ErrorAction SilentlyContinue
    }
}
"ambiente de teste carregado (valores não exibidos)"
