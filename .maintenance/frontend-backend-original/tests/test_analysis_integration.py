"""
Teste de integração do pipeline unificado (secção 32): upload de um CV real
(.docx) -> extração de texto -> NLP -> matching -> scoring -> persistência
-> ranking da vaga. Cobre o exemplo da secção 39 do prompt mestre.

Usa python-docx para gerar ficheiros de CV reais em memória — se a
biblioteca não estiver instalada no ambiente, os testes deste ficheiro
são ignorados (skip) em vez de falhar, já que é uma dependência opcional
de processamento de documentos (secção 34).
"""
import io

import pytest

docx = pytest.importorskip("docx", reason="python-docx não instalado neste ambiente")


def _make_docx(paragraphs: list[str]) -> io.BytesIO:
    document = docx.Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


def _upload_docx(client, headers, job_id, paragraphs, email, name="Candidato"):
    file_bytes = _make_docx(paragraphs)
    return client.post(
        f"/api/jobs/{job_id}/cvs",
        headers=headers,
        data={"candidate_name": name, "candidate_email": email},
        files={"file": ("cv.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )


def test_analyze_strong_candidate_is_recommended(client, recruiter_headers, job):
    """Réplica do exemplo da secção 2/39: candidato forte deve ficar 'Recomendado'."""
    upload = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=[
            "João Silva",
            "joao.forte@example.com",
            "4 anos de experiência como desenvolvedor backend.",
            "Desenvolveu APIs REST utilizando Laravel e PostgreSQL.",
            "Uso diário de PHP e Git em ambiente de produção.",
        ],
        email="joao.forte@example.com",
        name="João Silva",
    )
    resume_id = upload.json()["resumes"][0]["id"]

    response = client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_label"] == "Recomendado"
    assert data["overall_score"] >= 85.0
    assert data["mandatory_missing"] == []
    # Explicabilidade (secção 25): um item de breakdown por requisito da vaga
    assert len(data["breakdown"]) == len(job.requirements)


def test_analyze_weak_candidate_flags_missing_mandatory(client, recruiter_headers, job):
    upload = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=["Maria Pouco Match", "Experiência em atendimento ao cliente e vendas."],
        email="maria.fraca@example.com",
        name="Maria Pouco Match",
    )
    resume_id = upload.json()["resumes"][0]["id"]

    response = client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["recommendation_label"] == "Requisito obrigatório ausente"
    assert len(data["mandatory_missing"]) > 0


def test_get_analysis_before_analyzing_returns_404(client, recruiter_headers, job):
    upload = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=["Candidato sem análise ainda."],
        email="semanalise@example.com",
    )
    resume_id = upload.json()["resumes"][0]["id"]

    response = client.get(f"/api/cvs/{resume_id}/analysis", headers=recruiter_headers)
    assert response.status_code == 404


def test_ranking_orders_candidates_by_score(client, recruiter_headers, job):
    strong = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=[
            "4 anos de experiência.",
            "Desenvolveu APIs REST utilizando Laravel e PostgreSQL.",
            "PHP e Git no dia a dia.",
        ],
        email="forte@example.com", name="Candidato Forte",
    )
    weak = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=["Experiência em vendas."],
        email="fraco@example.com", name="Candidato Fraco",
    )

    for upload in (strong, weak):
        resume_id = upload.json()["resumes"][0]["id"]
        client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)

    response = client.get(f"/api/jobs/{job.id}/ranking", headers=recruiter_headers)
    assert response.status_code == 200
    ranking = response.json()

    assert len(ranking) == 2
    assert ranking[0]["candidate_email"] == "forte@example.com"
    assert ranking[1]["candidate_email"] == "fraco@example.com"
    assert ranking[0]["score"] > ranking[1]["score"]


def test_ranking_filter_by_label(client, recruiter_headers, job):
    upload = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=["Experiência em vendas."],
        email="filtro@example.com",
    )
    resume_id = upload.json()["resumes"][0]["id"]
    client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)

    response = client.get(
        f"/api/jobs/{job.id}/ranking",
        params={"filter": "requisito_obrigatorio_ausente"},
        headers=recruiter_headers,
    )
    assert response.status_code == 200
    assert all(item["recommendation_label"] == "Requisito obrigatório ausente" for item in response.json())

    response = client.get(
        f"/api/jobs/{job.id}/ranking",
        params={"filter": "recomendado"},
        headers=recruiter_headers,
    )
    assert response.json() == []


def test_reanalyzing_replaces_previous_match(client, recruiter_headers, job):
    """Re-analisar um CV não deve deixar registos de matching duplicados."""
    upload = _upload_docx(
        client, recruiter_headers, job.id,
        paragraphs=["Experiência em vendas."],
        email="reanalise@example.com",
    )
    resume_id = upload.json()["resumes"][0]["id"]

    client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)
    second = client.post(f"/api/cvs/{resume_id}/analyze", headers=recruiter_headers)
    assert second.status_code == 200

    response = client.get(f"/api/jobs/{job.id}/ranking", headers=recruiter_headers)
    matches = [item for item in response.json() if item["candidate_email"] == "reanalise@example.com"]
    assert len(matches) == 1
