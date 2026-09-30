import json
import re
from pydantic import ValidationError
from app.schemas.ai import GenerationConfig, QuestionnaireContent, Profile, Evaluation
from app.services.ai_provider import get_provider, ProviderError, SCHEMAS


def validate_citation(citation, sources):
    if citation.location not in sources or citation.quote not in sources[citation.location]:
        raise ProviderError("Citação sem suporte no documento original")


def run(operation, payload, provider=None):
    if operation not in SCHEMAS or len(json.dumps(payload)) > 200_000:
        raise ProviderError("Operação ou tamanho de entrada inválido")
    if operation == "questionnaire":
        config = GenerationConfig.model_validate(payload["config"])
        available = {r["id"]: r for r in payload["criteria"]["requirements"]}
        if not set(config.requirement_ids) <= available.keys():
            raise ProviderError("Competência não pertence aos critérios desta vaga")
        if config.category and any(available[i]["category"] != config.category for i in config.requirement_ids):
            raise ProviderError("Competências incompatíveis com a categoria escolhida")
    provider = provider or get_provider()
    try:
        output = SCHEMAS[operation].model_validate(provider.complete(operation, payload))
    except ValidationError as exc:
        fields = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or 'resposta'} ({error['type']})"
            for error in exc.errors(include_input=False, include_url=False)[:5]
        )
        raise ProviderError(f"Resposta do fornecedor não cumpre o contrato de {operation}: {fields}") from None
    except (ValueError, TypeError, KeyError):
        raise ProviderError("Resposta do fornecedor não cumpre o contrato") from None
    if isinstance(output, QuestionnaireContent):
        if output.language != config.language or len(output.questions) != config.count:
            raise ProviderError("Quantidade ou idioma divergente")
        for question in output.questions:
            if question.requirement_id not in config.requirement_ids or question.format != config.format:
                raise ProviderError("Pergunta fora da configuração")
            if question.category != available[question.requirement_id]["category"]:
                raise ProviderError("Categoria divergente")
            if not question.rubric or not question.expected_answer:
                raise ProviderError("Pergunta sem resposta esperada ou rubrica")
            question.provenance = "generated"
    else:
        sources = {source["location"]: source["text"] for source in payload["sources"]}
        if isinstance(output, Profile):
            for experience in output.experiences:
                validate_citation(experience.evidence, sources)
                if experience.employer and experience.employer.casefold() not in experience.evidence.quote.casefold():
                    raise ProviderError("Entidade empregadora sem suporte literal; requer revisão")
                for field in ("start", "end"):
                    value = getattr(experience, field)
                    if value and value.isoformat() not in experience.evidence.quote and value.strftime("%d/%m/%Y") not in experience.evidence.quote:
                        setattr(experience, field, None)  # Never invent date precision.
                if re.search(r"\b(curso|course|formação|training)\b", experience.evidence.quote, re.I):
                    raise ProviderError("Curso apresentado como experiência profissional; requer revisão")
            for fact in output.education + output.skills + output.languages:
                validate_citation(fact.evidence, sources)
            for fact in output.skills:
                if re.search(r"\b(não|not|never|sem|without)\b", fact.evidence.quote, re.I):
                    raise ProviderError("Competência com negação; requer revisão")
        elif isinstance(output, Evaluation):
            requirements = {r["id"]: r for r in payload["criteria"]["requirements"]}
            if sorted(e.requirement_id for e in output.evidence) != sorted(requirements):
                raise ProviderError("Avaliação incompleta ou com requisitos duplicados")
            for evidence in output.evidence:
                for citation in evidence.citations:
                    validate_citation(citation, sources)
                requirement = requirements[evidence.requirement_id]
                text = " ".join(c.quote for c in evidence.citations)
                if evidence.state in {"evidenced", "partial"}:
                    if re.search(r"\b(não|not|never|sem|without)\b", text, re.I):
                        evidence.state = "contradictory"
                        evidence.explanation = "O excerto contém negação; revisão humana necessária."
                    elif requirement["category"] in {"technology", "tool"} and not re.search(
                        r"(?<!\w)" + re.escape(requirement["name"]) + r"(?!\w)", text, re.I):
                        evidence.state = "not_evidenced"
                        evidence.explanation = "O produto específico não é mencionado na evidência citada."
    return output, provider.name
