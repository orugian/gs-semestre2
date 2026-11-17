"""Testes de bootstrapping local: ambiente_teste.ps1 e testar_tudo.ps1.

Verifica isolamento de escopo, higienizacao de variaveis herdadas,
bloqueio com instalacao parcial (uv sync / pnpm install), protecao de DSN externo
e integridade de caminhos sem vazar credenciais nem poluir ambiente.
"""

import os
import shutil
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" and shutil.which("powershell") is None,
    reason=(
        "Os scripts ambiente_teste.ps1 e testar_tudo.ps1 dependem do Windows PowerShell 5.1; "
        "em sistemas operacionais nao-Windows sem powershell no PATH, a suite e ignorada."
    ),
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FERRAMENTAS_ORIGEM = REPO_ROOT / "app" / "tools"

ENV_TESTE_VALIDO = (
    "ORACLE_TESTE_USER=CT_TESTE_S9\n"
    "ORACLE_TESTE_PASSWORD=fake_oracle_pass\n"
    "POSTGRES_TESTE_PASSWORD=fake_pg_pass\n"
    "MONGO_TESTE_PASSWORD=fake_mongo_pass\n"
    "ORACLE_DSN=127.0.0.1:1521/FREEPDB1\n"
)


def run_ps_cmd(
    cmd: str, cwd: Path | str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Executa um comando inline no Windows PowerShell 5.1 com politicas seguras."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )


def run_ps_script(
    script: Path | str,
    args: list[str] | None = None,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Executa um arquivo .ps1 no Windows PowerShell 5.1 com politicas seguras."""
    full_cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    ]
    if args:
        full_cmd.extend(args)
    return subprocess.run(
        full_cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )


def parse_bool_flags(stdout: str) -> dict[str, bool]:
    """Extrai flags booleanas no formato CHAVE:True/False sem expor conteudo ou tamanho."""
    flags: dict[str, bool] = {}
    for line in stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v_clean = v.strip().lower()
            if v_clean in ("true", "false"):
                flags[k.strip()] = v_clean == "true"
    return flags


def _criar_mock_bin(diretorio_bin: Path) -> Path:
    """Cria executaveis simulados de uv e pnpm em diretorio_bin para isolar testes.

    Registra %CD% para permitir assercoes discriminantes sobre os diretorios acionados.
    """
    diretorio_bin.mkdir(parents=True, exist_ok=True)

    uv_cmd = diretorio_bin / "uv.cmd"
    uv_cmd.write_text(
        "@echo off\r\n"
        'echo [%CD%] uv %* >> "%MOCK_LOG%"\r\n'
        'if "%1"=="sync" (\r\n'
        "  if defined MOCK_UV_SYNC_FAIL exit /b 1\r\n"
        ")\r\n"
        "exit /b 0\r\n",
        encoding="utf-8",
    )

    pnpm_cmd = diretorio_bin / "pnpm.cmd"
    pnpm_cmd.write_text(
        "@echo off\r\n"
        'echo [%CD%] pnpm %* >> "%MOCK_LOG%"\r\n'
        'if "%1"=="install" (\r\n'
        "  if defined MOCK_PNPM_INSTALL_FAIL exit /b 1\r\n"
        ")\r\n"
        "exit /b 0\r\n",
        encoding="utf-8",
    )

    return diretorio_bin


def _criar_arvore_projeto(
    pasta_raiz: Path,
    conteudo_env: str | None = None,
    criar_env: bool = True,
) -> tuple[Path, Path]:
    """Cria estrutura minima de projeto em pasta_raiz com scripts copiados de app/tools."""
    app_dir = pasta_raiz / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    tools_dir = app_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(
        FERRAMENTAS_ORIGEM / "ambiente_teste.ps1", tools_dir / "ambiente_teste.ps1"
    )
    shutil.copy(FERRAMENTAS_ORIGEM / "testar_tudo.ps1", tools_dir / "testar_tudo.ps1")

    for componente in ["api", "cloud", "tools", "ml", "web"]:
        (app_dir / componente).mkdir(parents=True, exist_ok=True)

    if criar_env:
        texto = ENV_TESTE_VALIDO if conteudo_env is None else conteudo_env
        (app_dir / ".env").write_text(texto, encoding="utf-8")

    return app_dir, tools_dir


@pytest.fixture
def mock_env(tmp_path: Path) -> Generator[dict[str, str], None, None]:
    """Ambiente com PATH mockado contendo uv e pnpm simulados e log de chamadas."""
    bin_dir = tmp_path / "mock_bin"
    _criar_mock_bin(bin_dir)
    log_file = tmp_path / "mock_calls.log"

    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["MOCK_LOG"] = str(log_file)
    env.pop("MOCK_UV_SYNC_FAIL", None)
    env.pop("MOCK_PNPM_INSTALL_FAIL", None)

    yield env


def test_uv_sync_failure_stops_regression_without_running_pytest(
    tmp_path: Path, mock_env: dict[str, str]
):
    """RED->GREEN: Se uv sync falhar, testar_tudo deve sair !=0 sem invocar pytest."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    mock_env["MOCK_UV_SYNC_FAIL"] = "1"
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0, (
        f"Esperava saida != 0, obteve {res.returncode}. stdout: {res.stdout}"
    )
    assert log_file.exists(), "Log de chamadas mock nao foi gerado."
    chamadas = log_file.read_text(encoding="utf-8")
    assert "--frozen" in chamadas, "uv sync deve utilizar a flag --frozen."
    assert "uv run" not in chamadas and "pytest -q" not in chamadas, (
        "uv run pytest nao deve ser executado quando uv sync falha."
    )


def test_pnpm_install_failure_stops_regression_without_running_web_tasks(
    tmp_path: Path, mock_env: dict[str, str]
):
    """RED->GREEN: Se pnpm install falhar, testar_tudo deve sair !=0 sem tarefas web."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    mock_env["MOCK_PNPM_INSTALL_FAIL"] = "1"
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0, (
        f"Esperava saida != 0, obteve {res.returncode}. stdout: {res.stdout}"
    )
    assert log_file.exists(), "Log de chamadas mock nao foi gerado."
    chamadas = log_file.read_text(encoding="utf-8")
    assert "pnpm run typecheck" not in chamadas, (
        "typecheck nao deve rodar se pnpm install falha."
    )
    assert "pnpm run test" not in chamadas, (
        "vitest nao deve rodar se pnpm install falha."
    )
    assert "pnpm run build" not in chamadas, (
        "build nao deve rodar se pnpm install falha."
    )


def test_testar_tudo_blocks_when_database_config_is_missing(
    tmp_path: Path, mock_env: dict[str, str]
):
    """Runner completo deve abortar explicitamente quando faltam credenciais de banco."""
    pasta_projeto = tmp_path / "proj"
    env_incompleto = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=\n"
        "POSTGRES_TESTE_PASSWORD=\n"
        "MONGO_TESTE_PASSWORD=\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_incompleto)
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0, "testar_tudo deve abortar quando faltam bancos."
    assert "Runner completo bloqueado" in (res.stderr + res.stdout)

    if log_file.exists():
        chamadas = log_file.read_text(encoding="utf-8")
        assert "uv sync" not in chamadas, (
            "Nao deve iniciar execucao se bancos estao ausentes."
        )


def test_ambiente_teste_does_not_pollute_caller_scope(tmp_path: Path):
    """Dot-sourcing ambiente_teste.ps1 nao deve vazar $v, $Matches nem variaveis internas."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    cmd = (
        "$varChamador = 'intacta'; "
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('VAR_CHAMADOR:' + $varChamador); "
        "Write-Output ('V_IS_NULL:' + ($null -eq $v)); "
        "Write-Output ('MATCHES_IS_NULL:' + ($null -eq $Matches)); "
        "Write-Output ('RAIZ_IS_NULL:' + ($null -eq $raiz)); "
        "Write-Output ('ARQUIVO_IS_NULL:' + ($null -eq $arquivo)); "
        "Write-Output ('FALTANDO_IS_NULL:' + ($null -eq $faltando)); "
        "Write-Output ('CHAVE_IS_NULL:' + ($null -eq $chave))"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto)
    assert res.returncode == 0, f"Erro ao executar PowerShell: {res.stderr}"

    assert "VAR_CHAMADOR:intacta" in res.stdout
    flags = parse_bool_flags(res.stdout)
    assert flags.get("V_IS_NULL") is True, f"$v vazou no escopo: {res.stdout}"
    assert flags.get("MATCHES_IS_NULL") is True, (
        f"$Matches vazou no escopo: {res.stdout}"
    )
    assert flags.get("RAIZ_IS_NULL") is True, (
        f"$raiz vazou no escopo: {res.stdout}"
    )
    assert flags.get("ARQUIVO_IS_NULL") is True, (
        f"$arquivo vazou no escopo: {res.stdout}"
    )
    assert flags.get("FALTANDO_IS_NULL") is True, (
        f"$faltando vazou no escopo: {res.stdout}"
    )
    assert flags.get("CHAVE_IS_NULL") is True, (
        f"$chave vazou no escopo: {res.stdout}"
    )


def test_ambiente_teste_comment_parsing_not_treated_as_password(tmp_path: Path):
    """Comentarios inline no .env (ex: # [GERADO]) nao devem ser interpretados como senha."""
    pasta_projeto = tmp_path / "proj"
    env_comentarios = (
        "ORACLE_TESTE_USER=CT_TESTE_S9                        # [FIXO] trava de teste\n"
        "ORACLE_TESTE_PASSWORD=                               # [GERADO]\n"
        "POSTGRES_TESTE_PASSWORD= # [GERADO] porta 5433\n"
        "MONGO_TESTE_PASSWORD=\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_comentarios)

    # Usa flags booleanas: nunca imprime senha nem comprimento de segredos
    cmd = (
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('ORACLE_USER_IS_EXPECTED:' + "
        "[string]($env:ORACLE_USER -eq 'CT_TESTE_S9')); "
        "Write-Output ('ORACLE_PASS_EMPTY:' + "
        "[string]([string]::IsNullOrEmpty($env:ORACLE_PASSWORD))); "
        "Write-Output ('PG_PASS_EMPTY:' + "
        "[string]([string]::IsNullOrEmpty($env:PG_TESTE_PASSWORD)))"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto)
    assert res.returncode == 0, f"Erro ao executar PowerShell: {res.stderr}"

    flags = parse_bool_flags(res.stdout)
    assert flags.get("ORACLE_USER_IS_EXPECTED") is True
    assert flags.get("ORACLE_PASS_EMPTY") is True, (
        f"Comentario tratado como senha Oracle: {res.stdout}"
    )
    assert flags.get("PG_PASS_EMPTY") is True, (
        f"Comentario tratado como senha PG: {res.stdout}"
    )
    assert "Sem valor em app/.env para: ORACLE_PASSWORD" in (
        res.stdout + res.stderr
    )


def test_ambiente_teste_rejects_external_dsn(tmp_path: Path):
    """DSN externo para Oracle deve ser rejeitado no modo de teste local."""
    pasta_projeto = tmp_path / "proj"
    env_dsn_externo = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        "ORACLE_DSN=db.externo.fiap.com.br:1521/PROD\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_dsn_externo)

    cmd = f". '{tools_dir / 'ambiente_teste.ps1'}'"
    res = run_ps_cmd(cmd, cwd=pasta_projeto)

    assert res.returncode != 0, "Deveria falhar ao receber DSN externo."
    assert "DSN externo não permitido" in (res.stderr + res.stdout)


def test_oracle_dsn_restricted_to_compose_endpoint_1521_freepdb1(
    tmp_path: Path,
):
    """Valida restricao estrita a 127.0.0.1 porta 1521 e FREEPDB1 antes de atribuir credenciais."""
    pasta_projeto = tmp_path / "proj"

    # Porta diferente (1522) deve ser recusada
    env_porta_invalida = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        "ORACLE_DSN=127.0.0.1:1522/FREEPDB1\n"
    )
    _, tools_dir = _criar_arvore_projeto(
        pasta_projeto / "porta", conteudo_env=env_porta_invalida
    )
    cmd = (
        f"$env:ORACLE_USER = 'NAO_ALTERAR'; . '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('ORACLE_USER_FLAG:' + [string]($env:ORACLE_USER -eq 'NAO_ALTERAR'))"
    )
    res = run_ps_cmd(cmd, cwd=pasta_projeto / "porta")
    assert res.returncode != 0, "Deveria rejeitar porta diferente de 1521."
    assert "DSN externo não permitido" in (res.stderr + res.stdout)


def test_ambiente_teste_clears_inherited_cloud_and_paid_credentials(
    tmp_path: Path,
):
    """Variaveis de servicos pagos, nuvem (AWS_*) e sentimento devem ser limpas ou desligadas."""
    pasta_projeto = tmp_path / "proj"
    env_com_servicos = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        "OPENROUTER_API_KEY=sk-tentativa-import\n"
        "HF_TOKEN=hf-tentativa-import\n"
        "FUNCTION_URL=https://tentativa.lambda\n"
    )
    _, tools_dir = _criar_arvore_projeto(
        pasta_projeto, conteudo_env=env_com_servicos
    )

    custom_env = os.environ.copy()
    custom_env["OPENROUTER_API_KEY"] = "sk-herdada"
    custom_env["HF_TOKEN"] = "hf-herdado"
    custom_env["ADZUNA_APP_ID"] = "adzuna-herdado"
    custom_env["ADZUNA_APP_KEY"] = "adzuna-key-herdada"
    custom_env["FUNCTION_URL"] = "https://url.lambda.aws.com"
    custom_env["AWS_ACCESS_KEY_ID"] = "ASIAFAKE"
    custom_env["AWS_SECRET_ACCESS_KEY"] = "fake_secret"
    custom_env["AWS_SESSION_TOKEN"] = "fake_token"
    custom_env["SENTIMENTO_PROVEDOR"] = "comprehend"

    # Usa flags booleanas: nunca imprime chaves, tokens nem seus comprimentos
    cmd = (
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('OPENROUTER_CLEARED:' + "
        "[string]([string]::IsNullOrEmpty($env:OPENROUTER_API_KEY))); "
        "Write-Output ('HF_CLEARED:' + "
        "[string]([string]::IsNullOrEmpty($env:HF_TOKEN))); "
        "Write-Output ('ADZUNA_ID_CLEARED:' + "
        "[string]([string]::IsNullOrEmpty($env:ADZUNA_APP_ID))); "
        "Write-Output ('ADZUNA_KEY_CLEARED:' + "
        "[string]([string]::IsNullOrEmpty($env:ADZUNA_APP_KEY))); "
        "Write-Output ('FUNCTION_URL_CLEARED:' + "
        "[string]([string]::IsNullOrEmpty($env:FUNCTION_URL))); "
        "Write-Output ('AWS_CLEARED:' + "
        "[string](@(Get-ChildItem env:AWS_* -ErrorAction SilentlyContinue).Count -eq 0)); "
        "Write-Output ('SENTIMENTO_DESLIGADO:' + "
        "[string]($env:SENTIMENTO_PROVEDOR -eq 'desligado'))"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto, env=custom_env)
    assert res.returncode == 0, f"Erro no script: {res.stderr}"

    flags = parse_bool_flags(res.stdout)
    assert flags.get("OPENROUTER_CLEARED") is True
    assert flags.get("HF_CLEARED") is True
    assert flags.get("ADZUNA_ID_CLEARED") is True
    assert flags.get("ADZUNA_KEY_CLEARED") is True
    assert flags.get("FUNCTION_URL_CLEARED") is True
    assert flags.get("AWS_CLEARED") is True
    assert flags.get("SENTIMENTO_DESLIGADO") is True


def test_ambiente_teste_generates_ephemeral_jwt_secret_and_device_key(
    tmp_path: Path,
):
    """JWT_SECRET efemero e DEVICE_KEY devem ser configurados sem imprimir valores."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    cmd = (
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('JWT_VALID:' + "
        "[string](([string]$env:JWT_SECRET).Length -ge 32)); "
        "Write-Output ('DEV_KEY_PRESENT:' + "
        "[string](-not [string]::IsNullOrEmpty($env:DEVICE_KEY)))"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto)
    assert res.returncode == 0, f"Erro: {res.stderr}"

    flags = parse_bool_flags(res.stdout)
    assert flags.get("JWT_VALID") is True, (
        f"JWT_SECRET deve ter >= 32 chars: {res.stdout}"
    )
    assert flags.get("DEV_KEY_PRESENT") is True, (
        f"DEVICE_KEY deve estar presente: {res.stdout}"
    )


def test_ambiente_teste_isolated_outbox_and_runtime(tmp_path: Path):
    """Runtime temporario novo por chamada para outbox, leituras e CITIZENTECH_DADOS."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    cmd = (
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('CSV:' + $env:CITIZENTECH_LEITURAS_CSV); "
        "Write-Output ('DB:' + $env:CITIZENTECH_OUTBOX_DB); "
        "Write-Output ('DADOS:' + $env:CITIZENTECH_DADOS)"
    )

    res1 = run_ps_cmd(cmd, cwd=pasta_projeto)
    res2 = run_ps_cmd(cmd, cwd=pasta_projeto)

    assert res1.returncode == 0
    assert res2.returncode == 0

    linhas1 = dict(
        line.split(":", 1)
        for line in res1.stdout.strip().splitlines()
        if ":" in line
    )
    linhas2 = dict(
        line.split(":", 1)
        for line in res2.stdout.strip().splitlines()
        if ":" in line
    )

    csv1 = Path(linhas1["CSV"])
    db1 = Path(linhas1["DB"])
    dados1 = Path(linhas1["DADOS"])

    csv2 = Path(linhas2["CSV"])
    db2 = Path(linhas2["DB"])
    dados2 = Path(linhas2["DADOS"])

    assert not csv1.exists(), "CSV de leituras nao deve preexistir."
    assert not db1.exists(), "outbox.db nao deve preexistir."
    assert csv1 != csv2, "Cada chamada deve gerar um runtime temporario novo."
    assert db1 != db2, "Cada chamada deve gerar um banco outbox novo."
    assert dados1 != dados2, (
        "Cada chamada deve isolar CITIZENTECH_DADOS em runtime proprio."
    )
    assert csv1.parent == dados1, (
        "CITIZENTECH_DADOS deve apontar para a pasta privada do runtime."
    )


def test_ambiente_teste_preserves_explicit_mercado_snapshot(tmp_path: Path):
    """Snapshot local de mercado explicitamente informado em app/.env deve ser preservado."""
    pasta_projeto = tmp_path / "proj"
    caminho_snap = r"C:\caminho\ficticio\snapshot_mercado"
    env_snap = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        f"CITIZENTECH_MERCADO_SNAPSHOT={caminho_snap}\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_snap)

    cmd = (
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('SNAP:' + $env:CITIZENTECH_MERCADO_SNAPSHOT)"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto)
    assert res.returncode == 0
    assert f"SNAP:{caminho_snap}" in res.stdout


def test_ambiente_teste_does_not_preserve_external_bancos_teste_faltando(
    tmp_path: Path,
):
    """Nao deve preservar BANCOS_TESTE_FALTANDO herdado de fora se o .env for valido."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    cmd = (
        "$env:BANCOS_TESTE_FALTANDO = 'BANCO_FAKE_HERDADO'; "
        f". '{tools_dir / 'ambiente_teste.ps1'}'; "
        "Write-Output ('FALTANDO_FLAG:' + "
        "[string]([string]::IsNullOrEmpty($env:BANCOS_TESTE_FALTANDO)))"
    )

    res = run_ps_cmd(cmd, cwd=pasta_projeto)
    assert res.returncode == 0
    flags = parse_bool_flags(res.stdout)
    assert flags.get("FALTANDO_FLAG") is True, (
        f"BANCOS_TESTE_FALTANDO foi preservado indevidamente: {res.stdout}"
    )


def test_runner_exits_nonzero_before_clis_when_env_file_missing_with_prior_valid_session(
    tmp_path: Path, mock_env: dict[str, str]
):
    """Sem .env, runner deve sair != 0 ANTES de qualquer CLI mesmo com vars de sessao validas."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, criar_env=False)

    mock_env["ORACLE_USER"] = "CT_TESTE_S9"
    mock_env["ORACLE_PASSWORD"] = "pass_anterior"
    mock_env["PG_TESTE_PASSWORD"] = "pass_anterior"
    mock_env["MONGO_TESTE_PASSWORD"] = "pass_anterior"
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0, (
        f"Runner deveria sair != 0 sem .env, obteve {res.returncode}"
    )
    if log_file.exists():
        chamadas = log_file.read_text(encoding="utf-8")
        assert "uv" not in chamadas and "pnpm" not in chamadas, (
            f"Nenhum CLI deveria ter sido executado: {chamadas}"
        )


def test_runner_exits_nonzero_before_clis_when_dsn_external_with_prior_valid_session(
    tmp_path: Path, mock_env: dict[str, str]
):
    """Com DSN externo, runner deve sair != 0 ANTES de qualquer CLI mesmo com vars de sessao."""
    pasta_projeto = tmp_path / "proj"
    env_dsn_externo = (
        "ORACLE_TESTE_USER=CT_TESTE_S9\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        "ORACLE_DSN=db.externo.fiap.com.br:1521/PROD\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_dsn_externo)

    mock_env["ORACLE_USER"] = "CT_TESTE_S9"
    mock_env["ORACLE_PASSWORD"] = "pass_anterior"
    mock_env["PG_TESTE_PASSWORD"] = "pass_anterior"
    mock_env["MONGO_TESTE_PASSWORD"] = "pass_anterior"
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0
    if log_file.exists():
        chamadas = log_file.read_text(encoding="utf-8")
        assert "uv" not in chamadas and "pnpm" not in chamadas, (
            f"Nenhum CLI deveria ter sido executado: {chamadas}"
        )


def test_runner_exits_nonzero_before_clis_when_oracle_teste_user_is_app_user(
    tmp_path: Path, mock_env: dict[str, str]
):
    """Com ORACLE_TESTE_USER de app em vez de CT_*TESTE*, runner sai != 0 ANTES de CLIs."""
    pasta_projeto = tmp_path / "proj"
    env_usuario_app = (
        "ORACLE_TESTE_USER=citizentech\n"
        "ORACLE_TESTE_PASSWORD=pass\n"
        "POSTGRES_TESTE_PASSWORD=pass\n"
        "MONGO_TESTE_PASSWORD=pass\n"
        "ORACLE_DSN=127.0.0.1:1521/FREEPDB1\n"
    )
    _, tools_dir = _criar_arvore_projeto(pasta_projeto, conteudo_env=env_usuario_app)

    mock_env["ORACLE_USER"] = "CT_TESTE_S9"
    mock_env["ORACLE_PASSWORD"] = "pass_anterior"
    mock_env["PG_TESTE_PASSWORD"] = "pass_anterior"
    mock_env["MONGO_TESTE_PASSWORD"] = "pass_anterior"
    log_file = Path(mock_env["MOCK_LOG"])

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=mock_env
    )

    assert res.returncode != 0
    if log_file.exists():
        chamadas = log_file.read_text(encoding="utf-8")
        assert "uv" not in chamadas and "pnpm" not in chamadas, (
            f"Nenhum CLI deveria ter sido executado: {chamadas}"
        )


def test_runner_fails_when_uv_or_pnpm_missing(tmp_path: Path):
    """uv/pnpm ausentes no PATH nao podem produzir exito."""
    pasta_projeto = tmp_path / "proj"
    _, tools_dir = _criar_arvore_projeto(pasta_projeto)

    # PATH sem uv nem pnpm (apenas system32 para o powershell funcionar)
    sys_dir = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    env_sem_ferramentas = {
        "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
        "PATH": str(sys_dir),
    }

    res = run_ps_script(
        tools_dir / "testar_tudo.ps1", cwd=pasta_projeto, env=env_sem_ferramentas
    )

    assert res.returncode != 0, (
        f"Deveria falhar sem uv/pnpm, obteve: {res.returncode}"
    )


def test_fixture_with_spaces_and_flags_sem_ml_and_com_e2e(
    tmp_path: Path, mock_env: dict[str, str]
):
    """Suporta caminhos com espacos, verifica cwd nos mocks e respeita as flags."""
    pasta_com_espacos = tmp_path / "pasta com espacos no nome"
    _, tools_dir = _criar_arvore_projeto(pasta_com_espacos)
    log_file = Path(mock_env["MOCK_LOG"])

    # 1. Execucao com -SemML (sem -ComE2E)
    res_sem_ml = run_ps_script(
        tools_dir / "testar_tudo.ps1",
        args=["-SemML"],
        cwd=pasta_com_espacos,
        env=mock_env,
    )
    assert res_sem_ml.returncode == 0, (
        f"Falha na execucao com -SemML: {res_sem_ml.stderr}"
    )
    chamadas1 = log_file.read_text(encoding="utf-8")
    assert r"\app\ml" not in chamadas1 and "/app/ml" not in chamadas1, (
        "app/ml nao deveria ser visitado com -SemML"
    )
    assert r"\app\api" in chamadas1 or "/app/api" in chamadas1, (
        "app/api deveria ter sido executado"
    )
    assert "playwright" not in chamadas1
    assert "uv run --frozen pytest" in chamadas1

    # 2. Execucao com -ComE2E
    log_file.unlink()
    res_com_e2e = run_ps_script(
        tools_dir / "testar_tudo.ps1",
        args=["-SemML", "-ComE2E"],
        cwd=pasta_com_espacos,
        env=mock_env,
    )
    assert res_com_e2e.returncode == 0, (
        f"Falha na execucao com -ComE2E: {res_com_e2e.stderr}"
    )
    chamadas2 = log_file.read_text(encoding="utf-8")
    assert "playwright test" in chamadas2
