"""Testes unitarios para os adaptadores de sentimento (comprehend, hf, desligado)."""

import json
import logging

from citizentech_cloud.sentimento import analisar_relato


def test_relato_vazio_ou_nulo_retorna_sem_relato():
    for texto in [None, "", "   ", "\n"]:
        res = analisar_relato(texto)
        assert res["sentimento"] is None
        assert res["confianca"] is None
        assert res["analise_status"] == "sem_relato"


def test_provedor_desligado():
    res = analisar_relato("Relato de teste", provedor="desligado")
    assert res["sentimento"] is None
    assert res["confianca"] is None
    assert res["analise_status"] == "desligado"
    assert res["provedor"] == "desligado"


def test_provedor_comprehend_com_cliente_falso():
    class ClienteComprehendFake:
        def detect_sentiment(self, Text, LanguageCode):
            assert LanguageCode == "pt"
            assert "alagamento" in Text
            return {
                "Sentiment": "NEGATIVE",
                "SentimentScore": {
                    "Positive": 0.0123,
                    "Negative": 0.987654,
                    "Neutral": 0.0001,
                    "Mixed": 0.0,
                },
            }

    res = analisar_relato(
        "Alerta de alagamento na rua",
        provedor="comprehend",
        cliente=ClienteComprehendFake(),
    )
    assert res["sentimento"] == "negative"
    assert res["confianca"] == 0.9877  # Arredondado a 4 casas decimais
    assert res["analise_status"] == "ok"
    assert res["provedor"] == "comprehend"


def test_provedor_hf_com_mock_urlopen(monkeypatch):
    monkeypatch.setenv("HF_API_URL", "https://api-fake-hf.com")
    monkeypatch.setenv("HF_MODEL", "modelo-sentimento")
    monkeypatch.setenv("HF_TOKEN", "fake-token-123")

    resposta_hf = [
        [
            {"label": "POSITIVE", "score": 0.05123},
            {"label": "NEGATIVE", "score": 0.94877},
        ]
    ]
    corpo_bytes = json.dumps(resposta_hf).encode("utf-8")

    class RespostaMock:
        def read(self):
            return corpo_bytes

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: RespostaMock())

    res = analisar_relato("Situacao critica no bairro", provedor="hf")
    assert res["sentimento"] == "negative"
    assert res["confianca"] == 0.9488
    assert res["analise_status"] == "ok"
    assert res["provedor"] == "hf"


def test_comprehend_erro_ou_timeout_nao_lanca_excecao(caplog):
    class ClienteComprehendErro:
        def detect_sentiment(self, **kwargs):
            raise TimeoutError("Timeout ao conectar com o servico")

    with caplog.at_level(logging.WARNING):
        res = analisar_relato(
            "Relato qualquer",
            provedor="comprehend",
            cliente=ClienteComprehendErro(),
        )

    assert res["sentimento"] is None
    assert res["confianca"] is None
    assert res["analise_status"] == "indisponivel"
    assert "Falha na analise de sentimento" in caplog.text


def test_hf_sem_url_configurada_usa_router_atual(monkeypatch):
    """O endpoint antigo api-inference foi desativado (410); o padrão deve ser o router."""
    chamadas = []

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'[[{"label": "negative", "score": 0.9}]]'

    def falso_urlopen(req, timeout=None):
        chamadas.append(req.full_url)
        return Resp()

    monkeypatch.delenv("HF_API_URL", raising=False)
    monkeypatch.delenv("HF_MODEL", raising=False)
    monkeypatch.setattr("urllib.request.urlopen", falso_urlopen)
    from citizentech_cloud.sentimento import analisar_relato

    analisar_relato("agua subindo", provedor="hf")
    assert chamadas == [
        "https://router.huggingface.co/hf-inference/models/"
        "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    ]
