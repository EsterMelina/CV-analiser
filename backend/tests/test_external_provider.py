import json

import httpx
import pytest

from app.core.config import settings
from app.services.ai_provider import get_provider, ProviderError, configuration_error
from app.services.ai_service import run
from app.services.executions import execution_timeout


@pytest.fixture
def external(monkeypatch):
    for key, value in {"AI_PROVIDER": "openai-compatible", "AI_ENDPOINT": "https://example.test/v1/chat/completions",
            "AI_MODEL": "fixture", "AI_API_KEY": "test-secret", "AI_REAL_ENABLED": True,
            "AI_DATA_APPROVED": True, "AI_TIMEOUT_SECONDS": 120}.items():
        monkeypatch.setattr(settings, key, value)
    client_type = httpx.Client

    def install(handler):
        monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_type(
            transport=httpx.MockTransport(handler), **kwargs))
    return install


def response(content, finish="stop"):
    return httpx.Response(200, json={"choices": [{"finish_reason": finish,
        "message": {"content": content}}]})


def test_external_evaluation_uses_exact_source_fragments(external):
    def handler(request):
        payload = json.loads(json.loads(request.content)["messages"][1]["content"])
        assert payload["input"]["sources"][0] == {"id": 1, "text": "Python para APIs."}
        return response(json.dumps({"evidence": [{"requirement_id": 1, "state": "evidenced",
            "explanation": "APIs em Python documentadas", "source_ids": [1]}]}))
    external(handler)
    result, _ = run("evaluate", {"sources": [{"location": "p1", "text": "Python para APIs."}],
        "criteria": {"requirements": [{"id": 1, "name": "Python", "category": "technology"}]}})
    assert result.evidence[0].citations[0].quote == "Python para APIs."
    assert result.evidence[0].citations[0].location == "p1"


def test_external_contract(external):
    def handler(request):
        assert str(request.url) == settings.AI_ENDPOINT
        assert request.headers["Authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == "fixture"
        assert body["response_format"] == {"type": "json_object"}
        assert json.loads(body["messages"][1]["content"])["operation"] == "profile"
        return response('{"experiences": [], "education": [], "skills": [], "languages": []}')
    external(handler)
    profile, name = run("profile", {"sources": []})
    assert profile.skills == []
    assert name == "openai-compatible:fixture"
    assert execution_timeout() == 270


@pytest.mark.parametrize("body,finish", [('{}', 'length'), ('invalid', 'stop'), ('[]', 'stop')])
def test_invalid_completion(external, body, finish):
    external(lambda request: response(body, finish))
    with pytest.raises(ProviderError):
        get_provider().complete("profile", {})


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 302])
def test_provider_error_is_sanitized(external, status):
    external(lambda request: httpx.Response(status, text="test-secret private CV"))
    with pytest.raises(ProviderError) as error:
        get_provider().complete("profile", {})
    assert "test-secret" not in str(error.value)
    assert "private CV" not in str(error.value)


@pytest.mark.parametrize("key,value", [("AI_API_KEY", ""), ("AI_MODEL", ""),
    ("AI_ENDPOINT", "http://example.test"), ("AI_ENDPOINT", "https://user:secret@example.test"),
    ("AI_REAL_ENABLED", False), ("AI_DATA_APPROVED", False)])
def test_incomplete_configuration_is_blocked(external, monkeypatch, key, value):
    monkeypatch.setattr(settings, key, value)
    assert configuration_error()
    with pytest.raises(ProviderError):
        get_provider().complete("profile", {})


def test_external_rejects_invented_citation(external):
    external(lambda request: response(json.dumps({"skills": [{"value": "Python",
        "evidence": {"location": "p1", "quote": "invented"}}]})))
    with pytest.raises(ProviderError, match="Citação sem suporte"):
        run("profile", {"sources": [{"location": "p1", "text": "Original document"}]})


def test_no_local_model_loaded_by_default(monkeypatch):
    import importlib.util
    from app.services import embeddings
    # conftest replaces the production factory globally to keep the suite offline.
    spec = importlib.util.spec_from_file_location("embeddings_under_test", embeddings.__file__)
    embeddings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(embeddings)
    monkeypatch.setattr(settings, "LOCAL_EMBEDDINGS_ENABLED", False)
    def fail():
        pytest.fail("Local model must not load")
    monkeypatch.setattr(embeddings, "_SentenceTransformerBackend", fail)
    assert isinstance(embeddings._get_backend(), embeddings._TfidfBackend)


def test_timeout(external):
    def handler(request):
        raise httpx.ReadTimeout("private CV", request=request)
    external(handler)
    with pytest.raises(ProviderError, match="tempo de resposta"):
        get_provider().complete("profile", {})


def test_response_limit(external):
    external(lambda request: httpx.Response(200, content=b"x" * 256_001))
    with pytest.raises(ProviderError, match="limite"):
        get_provider().complete("profile", {})
