"""
Extração de informação estruturada a partir do texto bruto do CV.

Abordagem em camadas (secção 14 do prompt mestre — "não depender apenas
de palavras-chave"):
  1. Normalização + correspondência por dicionário de sinónimos (rápido,
     alta precisão para termos conhecidos: "Python Developer",
     "programação em Python", "desenvolvimento Python" -> "python").
  2. Para competências da vaga que não sejam encontradas na camada 1,
     o motor de matching (matching_engine.py) usa similaridade semântica
     (embeddings.py) sobre o texto completo do CV como segunda camada.

Isto mantém a extração rápida e explicável, com a componente semântica
a cobrir os casos que o dicionário não prevê.
"""
import re
from dataclasses import dataclass, field

# Dicionário de competências conhecidas -> sinónimos/variações comuns em CVs
# em português e inglês. Facilmente extensível.
SKILLS_TAXONOMY: dict[str, dict] = {
    "python": {"category": "technical_skill", "synonyms": ["python", "django", "flask"]},
    "php": {"category": "technical_skill", "synonyms": ["php"]},
    "laravel": {"category": "technology", "synonyms": ["laravel"]},
    "javascript": {"category": "technical_skill", "synonyms": ["javascript", "js", "node.js", "nodejs"]},
    "typescript": {"category": "technical_skill", "synonyms": ["typescript", "ts"]},
    "react": {"category": "technology", "synonyms": ["react", "react.js", "reactjs"]},
    "sql": {"category": "technical_skill", "synonyms": ["sql", "consultas sql", "structured query language"]},
    "postgresql": {"category": "technology", "synonyms": ["postgresql", "postgres"]},
    "mysql": {"category": "technology", "synonyms": ["mysql"]},
    "mongodb": {"category": "technology", "synonyms": ["mongodb", "mongo"]},
    "rest api": {"category": "technical_skill", "synonyms": ["rest api", "api rest", "restful", "apis rest"]},
    "git": {"category": "tool", "synonyms": ["git", "github", "gitlab", "bitbucket"]},
    "docker": {"category": "tool", "synonyms": ["docker", "containers", "contentores"]},
    "kubernetes": {"category": "tool", "synonyms": ["kubernetes", "k8s"]},
    "aws": {"category": "technology", "synonyms": ["aws", "amazon web services"]},
    "azure": {"category": "technology", "synonyms": ["azure", "microsoft azure"]},
    "machine learning": {"category": "technical_skill", "synonyms": ["machine learning", "aprendizagem automática", "ml"]},
    "power bi": {"category": "tool", "synonyms": ["power bi", "powerbi"]},
    "excel": {"category": "tool", "synonyms": ["excel", "microsoft excel"]},
    "java": {"category": "technical_skill", "synonyms": ["java"]},
    "c#": {"category": "technical_skill", "synonyms": ["c#", "csharp", ".net"]},
}

# Sinónimos curtos que colidem com palavras comuns e por isso exigem
# correspondência por fronteira de palavra (evita falsos positivos como
# "Java" dentro de "JavaScript", ou "Excel" dentro do português "excelente").
_STRICT_BOUNDARY_SYNONYMS = {"java", "excel"}

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d{2,4}[\s-]?)?\d{2,3}[\s-]?\d{3}[\s-]?\d{3,4}")
_EXPERIENCE_YEARS_RE = re.compile(
    r"(\d+)\s*(?:\+)?\s*(?:anos?|years?)\s*(?:de\s+)?(?:experi[êe]ncia)?", re.IGNORECASE
)
_EDUCATION_KEYWORDS = [
    "licenciatura", "mestrado", "doutoramento", "bacharelato", "pós-graduação",
    "bachelor", "master", "phd", "doctorate", "mba",
]
_LANGUAGES = ["português", "inglês", "francês", "espanhol", "mandarim", "portuguese", "english", "french", "spanish"]


@dataclass
class ExtractedSkill:
    name: str
    category: str
    evidence_snippet: str
    confidence: float = 1.0


@dataclass
class ExtractedProfile:
    skills: list[ExtractedSkill] = field(default_factory=list)
    education_lines: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    experience_years_estimate: int | None = None
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)


def _snippet_around(text: str, index: int, radius: int = 60) -> str:
    start = max(0, index - radius)
    end = min(len(text), index + radius)
    return text[start:end].replace("\n", " ").strip()


def _find_synonym(lower_text: str, synonym: str) -> int:
    """
    Procura um sinónimo no texto. Para sinónimos curtos e ambíguos
    (ver _STRICT_BOUNDARY_SYNONYMS), exige fronteira de palavra para evitar
    falsos positivos (ex: "java" dentro de "javascript"). Para os restantes,
    mantém a correspondência por substring simples — é intencional: permite
    que "sql" seja encontrado dentro de "mysql"/"postgresql" (quem usa um
    SGBD relacional demonstra evidência de SQL).
    """
    s = synonym.lower()
    if s in _STRICT_BOUNDARY_SYNONYMS:
        match = re.search(r"(?<![a-z0-9à-ú])" + re.escape(s) + r"(?![a-z0-9à-ú])", lower_text)
        return match.start() if match else -1
    return lower_text.find(s)


def extract_skills(text: str) -> list[ExtractedSkill]:
    lower_text = text.lower()
    found: list[ExtractedSkill] = []
    for canonical, meta in SKILLS_TAXONOMY.items():
        for synonym in meta["synonyms"]:
            idx = _find_synonym(lower_text, synonym)
            if idx != -1:
                found.append(ExtractedSkill(
                    name=canonical,
                    category=meta["category"],
                    evidence_snippet=_snippet_around(text, idx),
                    confidence=1.0,
                ))
                break  # já encontrou este skill, não precisa testar outros sinónimos
    return found


def extract_education_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches = []
    for line in lines:
        lower = line.lower()
        if any(keyword in lower for keyword in _EDUCATION_KEYWORDS):
            matches.append(line)
    return matches


def extract_languages(text: str) -> list[str]:
    lower_text = text.lower()
    return [lang for lang in _LANGUAGES if lang in lower_text]


def extract_experience_years(text: str) -> int | None:
    """
    Heurística simples: procura padrões como "4 anos de experiência".
    Numa evolução futura, complementar com o cálculo de intervalos de
    datas nas experiências profissionais extraídas (secção 14).
    """
    matches = _EXPERIENCE_YEARS_RE.findall(text)
    years = [int(m) for m in matches if m.isdigit()]
    return max(years) if years else None


def extract_contact_info(text: str) -> tuple[list[str], list[str]]:
    emails = list(dict.fromkeys(_EMAIL_RE.findall(text)))
    phones = list(dict.fromkeys(_PHONE_RE.findall(text)))
    return emails, phones


def extract_profile(text: str) -> ExtractedProfile:
    emails, phones = extract_contact_info(text)
    return ExtractedProfile(
        skills=extract_skills(text),
        education_lines=extract_education_lines(text),
        languages=extract_languages(text),
        experience_years_estimate=extract_experience_years(text),
        emails=emails,
        phones=phones,
    )
