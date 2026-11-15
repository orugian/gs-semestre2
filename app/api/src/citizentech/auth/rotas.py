"""Rotas de autenticacao, sessao e dados do usuario logado (S5)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from citizentech.auth.csrf import gerar_token_csrf
from citizentech.auth.dependencias import exigir_csrf, obter_usuario_logado
from citizentech.auth.esquemas import (
    LoginRequisicao,
    LoginResposta,
    MeResposta,
    RegistroRequisicao,
    RegistroResposta,
)
from citizentech.auth.limitador import limitador_login
from citizentech.auth.repositorio import (
    buscar_por_email,
    criar_usuario,
    incrementar_sessao_versao,
)
from citizentech.auth.senhas import (
    executar_verificacao_ficticia,
    gerar_hash_senha,
    validar_politica_senha,
    verificar_senha,
)
from citizentech.auth.tokens import (
    criar_token_sessao,
    obter_expiracao_minutos,
    obter_jwt_secret,
)

router = APIRouter(tags=["autenticacao"])


@router.post(
    "/auth/registrar",
    response_model=RegistroResposta,
    status_code=status.HTTP_201_CREATED,
)
def registrar(payload: RegistroRequisicao) -> dict:
    """Cria uma nova conta de usuario.

    Aplica a politica de senhas e armazena com Argon2id no Oracle.
    Nao inicia sessao automatica (sem cookies).
    """
    # Fail-closed: verifica configuracoes de seguranca antes de qualquer gravacao
    obter_jwt_secret()
    obter_expiracao_minutos()

    validar_politica_senha(payload.senha)
    senha_hash = gerar_hash_senha(payload.senha)
    usuario_criado = criar_usuario(payload.email, senha_hash)
    return usuario_criado


@router.post(
    "/auth/login",
    response_model=LoginResposta,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequisicao,
    request: Request,
    response: Response,
) -> dict:
    """Autentica o usuario, aplica limitacao de taxa e emite cookies HttpOnly e CSRF."""
    # Fail-closed: verifica se a configuracao do segredo JWT e valida
    obter_jwt_secret()
    expira_minutos = obter_expiracao_minutos()

    # Valida politica de senhas e limite de 1024 bytes antes de trabalho caro (banco/Argon2)
    validar_politica_senha(payload.senha)

    ip_cliente = request.client.host if request.client else "127.0.0.1"

    # Limitador de taxa (D12, T16): max 5 tentativas/min por e-mail e por IP
    limitador_login.verificar_e_registrar(
        [f"email:{payload.email}", f"ip:{ip_cliente}"]
    )

    # Busca o usuario
    usuario = buscar_por_email(payload.email)
    if not usuario:
        # Prevencao de timing attack: executa verificacao contra hash ficticio
        executar_verificacao_ficticia(payload.senha)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Credenciais invalidas.",
            },
        )

    # Verifica senha
    if not verificar_senha(usuario["senha_hash"], payload.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "erro": "Nao autenticado",
                "detalhes": "Credenciais invalidas.",
            },
        )

    # Emissao de tokens e cookies seguros com a configuracao ja validada.
    max_age_segundos = expira_minutos * 60
    token_csrf = gerar_token_csrf()
    token_jwt = criar_token_sessao(
        usuario_id=usuario["id"],
        sessao_versao=usuario["sessao_versao"],
        csrf_token=token_csrf,
        expira_minutos=expira_minutos,
    )

    # Cookie de sessao: HttpOnly, Secure, SameSite=Lax
    response.set_cookie(
        key="sessao",
        value=token_jwt,
        max_age=max_age_segundos,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    # Cookie CSRF: legivel pelo JS para double-submit, Secure, SameSite=Lax
    response.set_cookie(
        key="csrf_token",
        value=token_csrf,
        max_age=max_age_segundos,
        httponly=False,
        secure=True,
        samesite="lax",
        path="/",
    )

    return {
        "id": usuario["id"],
        "email": usuario["email"],
    }


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(exigir_csrf)],
)
def logout(
    response: Response,
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> None:
    """Encerra a sessao do usuario, invalidando-a no servidor e limpando os cookies."""
    incrementar_sessao_versao(usuario["id"])

    response.delete_cookie(key="sessao", path="/", secure=True, samesite="lax")
    response.delete_cookie(key="csrf_token", path="/", secure=True, samesite="lax")


@router.get(
    "/me",
    response_model=MeResposta,
    status_code=status.HTTP_200_OK,
)
def obter_usuario_atual(
    usuario: Annotated[dict, Depends(obter_usuario_logado)],
) -> dict:
    """Retorna os dados cadastrais do usuario autenticado na sessao."""
    return {
        "id": usuario["id"],
        "email": usuario["email"],
        "criado_em": usuario["criado_em"],
        "persona_demo": usuario["persona_demo"],
    }
