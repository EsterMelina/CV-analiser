"""Reference source fragments by ID so local models need not regenerate the CV."""
import re
from typing import Literal
from pydantic import Field
from app.schemas.ai import StrictModel, Profile, ProfileFact


class CompactEvidence(StrictModel):
    requirement_id: int
    state: Literal["evidenced", "partial", "not_evidenced", "contradictory"]
    explanation: str = Field(min_length=1, max_length=400)
    source_ids: list[int] = Field(max_length=5)


class CompactEvaluation(StrictModel):
    evidence: list[CompactEvidence] = Field(max_length=100)


def prepare(payload):
    fragments = []
    for source in payload["sources"]:
        for line in re.split(r"\n+|(?<=[.!?])\s+", source["text"]):
            line = line.strip()
            for start in range(0, len(line), 600):
                fragments.append({"id": len(fragments) + 1, "location": source["location"], "text": line[start:start + 600]})
    criteria = payload["criteria"]
    compact_criteria = {"title": criteria.get("title"), "requirements": [
        {key: requirement[key] for key in ("id", "name", "category", "description", "expected_level") if key in requirement}
        for requirement in criteria.get("requirements", [])]}
    return {"criteria": compact_criteria, "sources": [
        {"id": fragment["id"], "text": fragment["text"]} for fragment in fragments]}, fragments


def expand(output, fragments):
    output = CompactEvaluation.model_validate(output)
    sources = {fragment["id"]: fragment for fragment in fragments}
    evidence = []
    for item in output.evidence:
        citations = []
        for source_id in dict.fromkeys(item.source_ids):
            if source_id not in sources:
                raise ValueError("Referência de evidência desconhecida")
            source = sources[source_id]
            citations.append({"location": source["location"], "quote": source["text"]})
        evidence.append({"requirement_id": item.requirement_id, "state": item.state,
                         "explanation": item.explanation, "citations": citations})
    return {"evidence": evidence}


def supported_profile(requirements, evaluation):
    """Only requirements fully supported by validated citations enter this summary."""
    profile = Profile()
    by_id = {requirement["id"]: requirement for requirement in requirements}
    categories = {"education": "education", "language": "languages", "technical_skill": "skills",
                  "technology": "skills", "tool": "skills"}
    for item in evaluation.evidence:
        requirement = by_id[item.requirement_id]
        category = categories.get(requirement["category"])
        if category and item.state == "evidenced" and item.citations:
            getattr(profile, category).append(ProfileFact(value=requirement["name"], evidence=item.citations[0]))
    return profile
