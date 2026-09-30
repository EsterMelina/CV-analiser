"""
Testes unitários do motor de matching (app/services/matching_engine.py).
Usa objetos simples (SimpleNamespace) em vez de instâncias reais do ORM,
para testar a lógica de matching/scoring isoladamente da base de dados.
"""
from types import SimpleNamespace

from app.services.matching_engine import compute_match


def _requirement(id, name, category, weight, is_mandatory, description=None):
    return SimpleNamespace(
        id=id, name=name, category=SimpleNamespace(value=category),
        weight=weight, is_mandatory=is_mandatory, description=description,
    )


def test_candidate_meeting_all_mandatory_requirements_is_recommended():
    """Exemplo da secção 2/39 do prompt mestre: candidato forte -> Recomendado."""
    requirements = [
        _requirement(1, "PHP", "technical_skill", 0.25, True),
        _requirement(2, "Laravel", "technology", 0.25, True),
        _requirement(3, "PostgreSQL", "technology", 0.20, True),
        _requirement(4, "Git", "tool", 0.10, False),
        _requirement(5, "Docker", "tool", 0.20, False),
    ]
    resume_text = (
        "Desenvolvedor com 4 anos de experiência.\n"
        "Desenvolveu APIs REST utilizando Laravel e PostgreSQL.\n"
        "Uso diário de PHP, Git e Docker em ambiente de produção."
    )

    result = compute_match(requirements, resume_text, min_experience_years=2)

    assert result.recommendation_label == "Recomendado"
    assert result.overall_score >= 85.0
    assert result.mandatory_missing == []


def test_missing_mandatory_requirement_overrides_high_score():
    """Secção 19: nunca esconder um requisito obrigatório em falta, mesmo com score alto."""
    requirements = [
        _requirement(1, "PHP", "technical_skill", 0.20, True),
        _requirement(2, "Laravel", "technology", 0.20, True),
        _requirement(3, "PostgreSQL", "technology", 0.20, True),
        _requirement(4, "Git", "tool", 0.20, True),
        _requirement(5, "Experiência mínima", "experience", 0.20, True),
    ]
    # Cumpre todas as competências técnicas mas não tem a experiência mínima exigida.
    resume_text = "Desenvolveu APIs REST utilizando Laravel, PHP, PostgreSQL e Git."

    result = compute_match(requirements, resume_text, min_experience_years=5)

    assert "Experiência mínima" in result.mandatory_missing
    assert result.recommendation_label == "Requisito obrigatório ausente"


def test_low_compatibility_candidate():
    requirements = [
        _requirement(1, "Python", "technical_skill", 0.5, True),
        _requirement(2, "Machine Learning", "technical_skill", 0.5, False),
    ]
    resume_text = "Experiência em vendas, atendimento ao cliente e gestão de equipas."

    result = compute_match(requirements, resume_text, min_experience_years=0)

    assert result.recommendation_label in {"Baixa compatibilidade", "Requisito obrigatório ausente"}
    assert result.overall_score < 65.0


def test_experience_requirement_partial_credit():
    """Candidato com menos anos que o exigido recebe contribuição proporcional, não zero."""
    requirements = [_requirement(1, "Experiência", "experience", 1.0, False)]

    result = compute_match(requirements, "Possui 2 anos de experiência.", min_experience_years=4)

    exp_result = result.requirement_results[0]
    assert exp_result.met is False
    assert 0.0 < exp_result.match_score < 1.0  # 2/4 = 0.5, não zero


def test_score_never_exceeds_100_or_goes_negative():
    requirements = [_requirement(1, "SQL", "technical_skill", 1.0, False)]
    result = compute_match(requirements, "SQL SQL SQL SQL", min_experience_years=0)
    assert 0.0 <= result.overall_score <= 100.0


def test_every_requirement_has_a_breakdown_entry():
    """Secção 25: toda recomendação deve ser explicável — um item de breakdown por requisito."""
    requirements = [
        _requirement(1, "Python", "technical_skill", 0.5, True),
        _requirement(2, "SQL", "technical_skill", 0.5, True),
    ]
    result = compute_match(requirements, "Experiência com Python e SQL.", min_experience_years=0)

    assert len(result.requirement_results) == len(requirements)
    for item in result.requirement_results:
        assert item.name in {"Python", "SQL"}
        assert item.contribution >= 0
