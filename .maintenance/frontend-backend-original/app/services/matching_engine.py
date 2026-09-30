"""
Motor de matching: compara os requisitos de uma vaga com o perfil extraído
de um candidato e produz um score explicável (secções 17, 18, 19, 25).

Regras principais respeitadas do prompt mestre:
- Requisitos obrigatórios são tratados/destacados separadamente (secção 19).
- Nunca esconder requisitos não cumpridos só porque o score é alto.
- Toda a pontuação vem com uma justificação (contribuições/lacunas).
- Não usar características pessoais irrelevantes (secção 35) — este motor
  nunca recebe nem considera nome, foto, género, idade, etc.
"""
from dataclasses import dataclass, field

from app.services.nlp_extraction import (
    ExtractedProfile, SKILLS_TAXONOMY, extract_skills,
    extract_education_lines, extract_languages, extract_experience_years,
)
from app.services.embeddings import semantic_similarity

# Abaixo deste score de similaridade semântica, um requisito sem correspondência
# exata no dicionário é considerado "não evidenciado" no CV.
SEMANTIC_MATCH_THRESHOLD = 0.35

RECOMMENDED_THRESHOLD = 85.0
EVALUATE_THRESHOLD = 65.0


@dataclass
class RequirementResult:
    requirement_id: int
    name: str
    category: str
    is_mandatory: bool
    weight: float
    met: bool
    match_score: float  # 0-1, usado para calcular a contribuição
    contribution: float  # pontos (0-100) que este requisito deu ao score final
    evidence: str | None


@dataclass
class MatchResult:
    overall_score: float
    recommendation_label: str
    requirement_results: list[RequirementResult]
    mandatory_missing: list[str]


def _normalize(text: str) -> str:
    return text.strip().lower()


def _skill_covers_requirement(requirement_name: str, profile_skill_names: set[str]) -> bool:
    normalized = _normalize(requirement_name)
    if normalized in profile_skill_names:
        return True
    # Verifica também se o nome do requisito é sinónimo de algum skill canónico já extraído
    for canonical, meta in SKILLS_TAXONOMY.items():
        if normalized in [_normalize(s) for s in meta["synonyms"]] and canonical in profile_skill_names:
            return True
    return False


def _evaluate_skill_like_requirement(
    requirement_name: str,
    requirement_description: str | None,
    profile: ExtractedProfile,
    resume_text: str,
) -> tuple[bool, float, str | None]:
    profile_skill_names = {s.name for s in profile.skills}

    if _skill_covers_requirement(requirement_name, profile_skill_names):
        evidence = next((s.evidence_snippet for s in profile.skills if s.name == _normalize(requirement_name)), None)
        return True, 1.0, evidence

    # Camada 2: similaridade semântica sobre o texto completo do CV (secção 16)
    query = f"{requirement_name}. {requirement_description or ''}"
    score = semantic_similarity(query, resume_text)
    met = score >= SEMANTIC_MATCH_THRESHOLD
    evidence = "Evidência semântica encontrada no texto do CV" if met else None
    return met, score, evidence


def _evaluate_experience_requirement(min_years_required: int, profile: ExtractedProfile) -> tuple[bool, float, str | None]:
    candidate_years = profile.experience_years_estimate
    if candidate_years is None:
        return False, 0.0, None
    if min_years_required <= 0:
        return True, 1.0, f"{candidate_years} anos de experiência identificados"
    ratio = min(1.0, candidate_years / min_years_required)
    met = candidate_years >= min_years_required
    evidence = f"{candidate_years} anos de experiência identificados (mínimo exigido: {min_years_required})"
    return met, ratio, evidence


def _evaluate_education_requirement(requirement_name: str, profile: ExtractedProfile, resume_text: str) -> tuple[bool, float, str | None]:
    if not profile.education_lines:
        # Sem linhas de formação claramente identificadas; tenta semântica sobre o CV completo
        score = semantic_similarity(requirement_name, resume_text)
        return score >= SEMANTIC_MATCH_THRESHOLD, score, None

    combined = " ".join(profile.education_lines)
    score = semantic_similarity(requirement_name, combined)
    met = score >= SEMANTIC_MATCH_THRESHOLD
    evidence = profile.education_lines[0] if met else None
    return met, score, evidence


def compute_match(
    requirements: list,  # list[app.models.job_requirement.JobRequirement]
    resume_text: str,
    min_experience_years: int = 0,
) -> MatchResult:
    profile = ExtractedProfile(
        skills=extract_skills(resume_text),
        education_lines=extract_education_lines(resume_text),
        languages=extract_languages(resume_text),
        experience_years_estimate=extract_experience_years(resume_text),
        emails=[],
        phones=[],
    )

    total_weight = sum(r.weight for r in requirements) or 1.0
    results: list[RequirementResult] = []
    mandatory_missing: list[str] = []

    for req in requirements:
        category = req.category.value if hasattr(req.category, "value") else str(req.category)

        if category == "experience":
            met, match_score, evidence = _evaluate_experience_requirement(min_experience_years, profile)
        elif category == "education":
            met, match_score, evidence = _evaluate_education_requirement(req.name, profile, resume_text)
        else:
            met, match_score, evidence = _evaluate_skill_like_requirement(req.name, req.description, profile, resume_text)

        normalized_weight = req.weight / total_weight
        contribution = normalized_weight * match_score * 100.0

        results.append(RequirementResult(
            requirement_id=req.id,
            name=req.name,
            category=category,
            is_mandatory=req.is_mandatory,
            weight=req.weight,
            met=met,
            match_score=round(match_score, 3),
            contribution=round(contribution, 2),
            evidence=evidence,
        ))

        if req.is_mandatory and not met:
            mandatory_missing.append(req.name)

    overall_score = round(sum(r.contribution for r in results), 2)
    overall_score = max(0.0, min(100.0, overall_score))

    if mandatory_missing:
        recommendation_label = "Requisito obrigatório ausente"
    elif overall_score >= RECOMMENDED_THRESHOLD:
        recommendation_label = "Recomendado"
    elif overall_score >= EVALUATE_THRESHOLD:
        recommendation_label = "Avaliar"
    else:
        recommendation_label = "Baixa compatibilidade"

    return MatchResult(
        overall_score=overall_score,
        recommendation_label=recommendation_label,
        requirement_results=results,
        mandatory_missing=mandatory_missing,
    )
