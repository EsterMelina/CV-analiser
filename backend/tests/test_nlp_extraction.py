"""
Testes unitários da camada de extração de NLP (app/services/nlp_extraction.py).
Não usam base de dados — testam apenas as funções puras de extração.
"""
from app.services.nlp_extraction import (
    extract_skills, extract_education_lines, extract_languages,
    extract_experience_years, extract_contact_info, extract_profile,
)


def test_extract_skills_recognizes_synonyms():
    """Secção 15: 'programação em Python', 'desenvolvimento Python' e
    'Python Developer' devem ser todos reconhecidos como a competência 'python'."""
    text = "Tenho experiência em desenvolvimento Python e também trabalhei com Django."
    skills = extract_skills(text)
    names = {s.name for s in skills}
    assert "python" in names


def test_extract_skills_from_master_prompt_example():
    """Exemplo literal da secção 15 do prompt mestre."""
    text = "Desenvolveu APIs REST utilizando Laravel e PostgreSQL."
    skills = {s.name for s in extract_skills(text)}
    assert "laravel" in skills
    assert "postgresql" in skills
    assert "rest api" in skills


def test_extract_skills_returns_evidence_snippet():
    text = "Sólida experiência com Docker e Kubernetes em ambientes de produção."
    skills = extract_skills(text)
    docker = next(s for s in skills if s.name == "docker")
    assert "docker" in docker.evidence_snippet.lower()


def test_extract_skills_no_false_positive():
    text = "Experiência em vendas e atendimento ao cliente."
    skills = {s.name for s in extract_skills(text)}
    assert "python" not in skills
    assert "laravel" not in skills


def test_java_detected_when_comma_follows():
    """Regressão: 'Java,' (vírgula, não espaço) tinha de ser detetado."""
    skills = {s.name for s in extract_skills("Linguagens: C, C++, Java, JavaScript.")}
    assert "java" in skills
    assert "javascript" in skills


def test_java_not_falsely_detected_inside_javascript_only():
    """Regressão: sem 'Java' isolado, não deve inferir 'java' só por causa de 'JavaScript'."""
    skills = {s.name for s in extract_skills("Experiência com JavaScript e Node.js.")}
    assert "java" not in skills
    assert "javascript" in skills


def test_excel_not_falsely_detected_inside_excelente():
    """Regressão: 'excelente' (PT) não deve disparar a competência 'Excel'."""
    skills = {s.name for s in extract_skills("Tenho excelente capacidade de comunicação.")}
    assert "excel" not in skills


def test_extract_education_lines():
    text = "Formação:\nLicenciatura em Informática, Universidade Eduardo Mondlane\nCurso de férias em vendas"
    lines = extract_education_lines(text)
    assert any("licenciatura" in line.lower() for line in lines)
    assert not any("curso de férias em vendas" == line.lower() for line in lines)


def test_extract_languages():
    text = "Idiomas: Português (nativo), Inglês (avançado)"
    languages = extract_languages(text)
    assert "português" in languages
    assert "inglês" in languages


def test_extract_experience_years():
    assert extract_experience_years("Possui 4 anos de experiência em desenvolvimento backend.") == 4
    assert extract_experience_years("3+ anos de experiência com bases de dados.") == 3
    assert extract_experience_years("Sem menção a experiência.") is None


def test_extract_experience_years_picks_the_largest_mention():
    text = "2 anos como estagiário e depois 5 anos como desenvolvedor sénior."
    assert extract_experience_years(text) == 5


def test_extract_contact_info():
    text = "Contacto: joao.silva@example.com | Tel: 84 123 4567"
    emails, phones = extract_contact_info(text)
    assert "joao.silva@example.com" in emails
    assert len(phones) >= 1


def test_extract_profile_combines_everything():
    text = (
        "João Silva\njoao@example.com\n"
        "Formação: Licenciatura em Informática\n"
        "4 anos de experiência em Python e SQL.\n"
        "Idiomas: Português, Inglês"
    )
    profile = extract_profile(text)
    assert profile.experience_years_estimate == 4
    assert "joao@example.com" in profile.emails
    assert {"python", "sql"}.issubset({s.name for s in profile.skills})
    assert "português" in profile.languages
