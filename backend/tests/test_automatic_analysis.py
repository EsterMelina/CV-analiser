import json
import httpx
import pytest
from app.core.config import settings
from app.services.ai_provider import OllamaProvider, ProviderError
from app.services.executions import process_one, execution_timeout
from app.services.scoring import calculate_score
from test_analysis_integration import _upload_docx


@pytest.mark.parametrize("score,mandatory,state,label", [
    (100, True, "evidenced", "Recomendado"),
    (50, False, "partial", "Compatibilidade parcial"),
    (0, False, "not_evidenced", "Baixa compatibilidade"),
    (50, True, "partial", "Requisito obrigatório ausente"),
])
def test_automatic_recommendation(score, mandatory, state, label):
    result = calculate_score([{"id": 1, "name": "Python", "weight": 1, "is_mandatory": mandatory}],
                             [{"requirement_id": 1, "state": state}])
    assert result["score"] == score
    assert result["recommendation"] == label
    assert "Revisão" not in result["summary"]


def test_mock_is_rejected_before_enqueuing_outside_tests(client, recruiter_headers, job, monkeypatch):
    application = _upload_docx(client, recruiter_headers, job.id, ["Python"], "automatic@example.com").json()
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    response = client.post(f'/api/cvs/{application["resumes"][0]["id"]}/analysis-executions',
        headers={**recruiter_headers, "Idempotency-Key": "no-mock"})
    assert response.status_code == 503
    assert client.get("/api/analysis-configuration", headers=recruiter_headers).json()["ready"] is False


def test_real_result_completes_and_reaches_ranking_without_review(client, recruiter_headers, job, db_session):
    text = "PHP Laravel PostgreSQL Git"
    application = _upload_docx(client, recruiter_headers, job.id, [text], "automatic@example.com").json()

    class RealContractFixture:
        name = "ollama:fixture"
        assessment_only = True
        def complete(self, operation, payload):
            assert operation == "evaluate"
            return {"evidence": [{"requirement_id": r["id"], "state": "evidenced",
                "explanation": "Competencia documentada", "citations": [
                    {"location": payload["sources"][0]["location"], "quote": payload["sources"][0]["text"]}]
                } for r in payload["criteria"]["requirements"]]}

    assert client.post(f'/api/cvs/{application["resumes"][0]["id"]}/analysis-executions',
        headers={**recruiter_headers, "Idempotency-Key": "automatic"}).status_code == 202
    process_one(db_session, RealContractFixture())
    history = client.get(f'/api/applications/{application["id"]}/analysis-runs', headers=recruiter_headers).json()
    assert history[0]["status"] == "completed"
    assert history[0]["result"]["profile_scope"] == "supported_requirements"
    assert history[0]["score"] is not None
    ranking = client.get(f'/api/jobs/{job.id}/ranking', headers=recruiter_headers).json()[0]
    assert ranking["recommendation_label"] == history[0]["result"]["recommendation"]
    assert ranking["analysis_status"] == "completed"
    assert ranking["status"] == "received"  # Assessment does not fabricate an interview or hiring event.


def configure_ollama(monkeypatch):
    for key, value in {"AI_PROVIDER": "ollama", "AI_ENDPOINT": "http://127.0.0.1:11434",
                       "AI_MODEL": "qwen2.5:7b", "AI_REAL_ENABLED": True, "AI_DATA_APPROVED": True}.items():
        monkeypatch.setattr(settings, key, value)


def test_ollama_contract_and_deadline(monkeypatch):
    configure_ollama(monkeypatch)
    client_class = httpx.Client
    def handler(request):
        assert str(request.url) == "http://127.0.0.1:11434/api/generate"
        body = json.loads(request.content)
        assert body["model"] == "qwen2.5:7b"
        assert body["stream"] is False
        assert body["format"]["type"] == "object"
        return httpx.Response(200, json={"done": True, "done_reason": "stop", "response": '{"skills": []}'})
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handler), **kwargs))
    assert OllamaProvider().complete("profile", {"sources": []}) == {"skills": []}
    assert execution_timeout() > 2 * settings.AI_TIMEOUT_SECONDS


def test_ollama_rejects_remote_endpoint(monkeypatch):
    configure_ollama(monkeypatch)
    monkeypatch.setattr(settings, "AI_ENDPOINT", "http://remote.example.com")
    with pytest.raises(ProviderError, match="local"):
        OllamaProvider().complete("profile", {})


def test_ollama_streaming_evaluation_reconstructs_citations(monkeypatch):
    configure_ollama(monkeypatch)
    client_class = httpx.Client
    response = json.dumps({"evidence": [{"requirement_id": 1, "state": "evidenced",
        "explanation": "Python documentado", "source_ids": [1]}]})
    def handler(request):
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, text='\n'.join([
            json.dumps({"response": response[:40], "done": False}),
            json.dumps({"response": response[40:], "done": True, "done_reason": "stop"})]))
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handler), **kwargs))
    output = OllamaProvider().complete("evaluate", {"sources": [{"location": "p1", "text": "Python documentado."}],
        "criteria": {"requirements": [{"id": 1, "name": "Python", "category": "technology"}]}})
    assert output["evidence"][0]["citations"] == [{"location": "p1", "quote": "Python documentado."}]


def test_ollama_incomplete_stream_is_not_a_completed_analysis(monkeypatch):
    configure_ollama(monkeypatch)
    client_class = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text=json.dumps({"response": '{"evidence":', "done": False}))), **kwargs))
    with pytest.raises(ProviderError, match="concluiu"):
        OllamaProvider().complete("evaluate", {"sources": [], "criteria": {"requirements": []}})
