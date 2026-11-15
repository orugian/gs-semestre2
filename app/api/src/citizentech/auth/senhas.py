"""Politica, derivacao e verificacao segura de senhas com Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import HTTPException, status

_hasher = PasswordHasher()
# Hash ficticio gerado uma vez no carregamento para garantir tempo constante no login
_HASH_FICTICIO = _hasher.hash("senha-ficticia-prevencao-timing-attack-12345")


def validar_politica_senha(senha: str) -> None:
    """Valida a politica de senha antes de qualquer computacao pesada de hash.

    Regras:
    - Rejeita com 400 se o tamanho em bytes exceder 1024 (previne abuso de CPU).
    - Exige entre 10 e 128 caracteres.
    """
    if not isinstance(senha, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "A senha informada e invalida.",
            },
        )

    tamanho_bytes = len(senha.encode("utf-8"))
    if tamanho_bytes > 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "A senha excede o limite maximo de tamanho permitido.",
            },
        )

    if not (10 <= len(senha) <= 128):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "erro": "Requisicao invalida",
                "detalhes": "A senha deve conter entre 10 e 128 caracteres.",
            },
        )


def gerar_hash_senha(senha: str) -> str:
    """Gera hash seguro com Argon2id."""
    return _hasher.hash(senha)


def verificar_senha(hash_armazenado: str, senha: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    try:
        return _hasher.verify(hash_armazenado, senha)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def executar_verificacao_ficticia(senha: str) -> None:
    """Executa verificacao contra hash ficticio para mitigar enumeracao de contas por timing."""
    try:
        _hasher.verify(_HASH_FICTICIO, senha)
    except Exception:
        pass
