# Dockerfile para CitizenTech API (FIAP GS 2026.2 - S3)
FROM python:3.11-slim

# Instala uv a partir da imagem oficial do Astral
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Cria usuario de sistema nao-root e diretorio de runtime
RUN groupadd -r citizentech && useradd -r -g citizentech -m -s /bin/bash citizentech \
    && mkdir -p /var/lib/citizentech/runtime \
    && chown -R citizentech:citizentech /var/lib/citizentech

# Copia definicoes de dependencias da API
COPY api/pyproject.toml api/uv.lock api/.python-version /app/api/

WORKDIR /app/api

# Pre-instala dependencias em ambiente virtual sem desenvolvimento
RUN uv sync --frozen --no-dev --no-install-project

# Copia configuracao global compartilhada (limiares) e codigo da API
COPY config /app/config
COPY api/src /app/api/src
COPY api/README.md /app/api/

# Sincroniza instalacao final do projeto
RUN uv sync --frozen --no-dev

ENV PATH="/app/api/.venv/bin:$PATH"
ENV CITIZENTECH_DADOS=/var/lib/citizentech
ENV CITIZENTECH_LIMIARES=/app/config/limiares.json

USER citizentech

EXPOSE 8000

CMD ["uvicorn", "citizentech.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
