"""Esquemas de validacao e respostas para autenticacao e perfil."""

import re

from pydantic import BaseModel, ConfigDict, field_validator

# Regex RFC 5322 simplificada para validacao de e-mail sem bibliotecas de rede
_PADRAO_EMAIL = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
)


def normalizar_e_validar_email(valor: str) -> str:
    """Normaliza (strip + minusculas) e valida o formato e tamanho do e-mail.

    Nunca ecoa o e-mail recebido na mensagem de erro para proteger dados pessoais.
    """
    if not isinstance(valor, str):
        raise ValueError("O e-mail deve ser uma cadeia de caracteres.")

    email_limpo = valor.strip().lower()
    if not email_limpo:
        raise ValueError("O e-mail e obrigatorio.")

    if len(email_limpo) > 254:
        raise ValueError("O e-mail excede o tamanho maximo de 254 caracteres.")

    if not _PADRAO_EMAIL.match(email_limpo):
        raise ValueError("O formato do e-mail e invalido.")

    return email_limpo


class RegistroRequisicao(BaseModel):
    """Payload para registro de nova conta de usuario."""

    model_config = ConfigDict(extra="forbid")

    email: str
    senha: str

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        return normalizar_e_validar_email(v)


class LoginRequisicao(BaseModel):
    """Payload para autenticacao de usuario."""

    model_config = ConfigDict(extra="forbid")

    email: str
    senha: str

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        return normalizar_e_validar_email(v)


class RegistroResposta(BaseModel):
    """Resposta de criacao de conta (201 Created)."""

    id: str
    email: str
    criado_em: str


class LoginResposta(BaseModel):
    """Resposta de autenticacao bem-sucedida (200 OK)."""

    id: str
    email: str


class MeResposta(BaseModel):
    """Dados cadastrais do usuario autenticado (GET /me)."""

    id: str
    email: str
    criado_em: str
    persona_demo: str
