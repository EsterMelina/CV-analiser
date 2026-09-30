"""Versioned contracts. Provider output is untrusted data, never commands."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Citation(StrictModel):
    location: str = Field(min_length=1, max_length=100)
    quote: str = Field(min_length=1, max_length=2000)


class Experience(StrictModel):
    employer: str | None = None
    activity: str = Field(min_length=1, max_length=1000)
    start: date | None = None
    end: date | None = None
    evidence: Citation

    @model_validator(mode="after")
    def dates(self):
        if self.start and self.end and self.end < self.start:
            raise ValueError("Datas invertidas")
        return self


class ProfileFact(StrictModel):
    value: str = Field(min_length=1, max_length=1000)
    evidence: Citation


class Profile(StrictModel):
    experiences: list[Experience] = Field(default_factory=list, max_length=100)
    education: list[ProfileFact] = Field(default_factory=list, max_length=100)
    skills: list[ProfileFact] = Field(default_factory=list, max_length=100)
    languages: list[ProfileFact] = Field(default_factory=list, max_length=50)


class Evidence(StrictModel):
    requirement_id: int
    state: Literal["evidenced", "partial", "not_evidenced", "contradictory"]
    explanation: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def supported(self):
        if self.state != "not_evidenced" and not self.citations:
            raise ValueError("Evidência sem citação")
        return self


class Evaluation(StrictModel):
    evidence: list[Evidence] = Field(max_length=100)


class Question(StrictModel):
    key: str = Field(min_length=1, max_length=80)
    requirement_id: int
    category: str = Field(min_length=1, max_length=80)
    format: Literal["open", "single_choice"] = "open"
    prompt: str = Field(min_length=5, max_length=4000)
    options: list[str] = Field(default_factory=list, max_length=6)
    correct_index: int | None = Field(default=None, ge=0)
    expected_answer: str = Field(default="", max_length=4000)
    rubric: str = Field(default="", max_length=4000)
    provenance: Literal["manual", "generated", "edited"] = "manual"

    @model_validator(mode="after")
    def valid_answer(self):
        if self.format == "single_choice":
            if len(self.options) < 2 or any(not option.strip() or len(option) > 1000 for option in self.options):
                raise ValueError("Opções inválidas")
            if len({option.strip().casefold() for option in self.options}) != len(self.options):
                raise ValueError("Opções repetidas")
            if self.correct_index is None or self.correct_index >= len(self.options):
                raise ValueError("Chave de resposta inválida")
        elif self.options or self.correct_index is not None:
            raise ValueError("Pergunta aberta não tem opções nem índice de resposta")
        return self


class QuestionnaireContent(StrictModel):
    language: Literal["pt", "en"] = "pt"
    questions: list[Question] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def unique_questions(self):
        keys = [q.key for q in self.questions]
        prompts = [q.prompt.casefold() for q in self.questions]
        if len(keys) != len(set(keys)) or len(prompts) != len(set(prompts)):
            raise ValueError("Perguntas repetidas")
        return self


class GeneratedQuestion(Question):
    expected_answer: str = Field(min_length=1, max_length=4000)
    rubric: str = Field(min_length=1, max_length=4000)


class GeneratedQuestionnaire(QuestionnaireContent):
    language: Literal["pt", "en"]
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=30)


class GenerationConfig(StrictModel):
    requirement_ids: list[int] = Field(min_length=1, max_length=30)
    category: str | None = None
    format: Literal["open", "single_choice"] = "open"
    count: int = Field(default=5, ge=1, le=30)
    difficulty: Literal["basic", "intermediate", "advanced"] = "intermediate"
    language: Literal["pt", "en"] = "pt"
