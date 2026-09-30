"""
Camada de similaridade semântica (secção 16 do prompt mestre).

Por defeito usa TF-IDF, sem carregar nem descarregar modelos locais.
Só tenta usar Sentence Transformers se LOCAL_EMBEDDINGS_ENABLED=true.
Se o pacote ou o modelo não estiverem disponíveis (ex: sem acesso à
internet para descarregar o modelo na primeira utilização), recorre
automaticamente a um fallback TF-IDF + similaridade de cosseno, que não
requer download de modelos e funciona totalmente offline.

Isto garante que o motor de matching nunca falha por falta de um modelo,
apenas com qualidade semântica reduzida — a app deve continuar a
funcionar (ver secção 40 "escalabilidade" / robustez).
"""
from functools import lru_cache
from app.core.config import settings

_SENTENCE_TRANSFORMER_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class _EmbeddingBackend:
    def similarity(self, text_a: str, text_b: str) -> float:
        raise NotImplementedError


class _SentenceTransformerBackend(_EmbeddingBackend):
    def __init__(self):
        from sentence_transformers import SentenceTransformer, util  # noqa
        self._util = util
        self._model = SentenceTransformer(_SENTENCE_TRANSFORMER_MODEL_NAME)

    def similarity(self, text_a: str, text_b: str) -> float:
        embeddings = self._model.encode([text_a, text_b], convert_to_tensor=True)
        score = self._util.cos_sim(embeddings[0], embeddings[1]).item()
        return max(0.0, min(1.0, score))  # cosine zero must not become 50% similarity


class _TfidfBackend(_EmbeddingBackend):
    """Fallback 100% offline. Menos rico semanticamente, mas robusto."""

    def similarity(self, text_a: str, text_b: str) -> float:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        a, b = (text_a or "").strip(), (text_b or "").strip()
        if not a or not b:
            return 0.0

        vectorizer = TfidfVectorizer().fit([a, b])
        vectors = vectorizer.transform([a, b])
        score = cosine_similarity(vectors[0], vectors[1])[0][0]
        return float(max(0.0, min(1.0, score)))


@lru_cache
def _get_backend() -> _EmbeddingBackend:
    if not settings.LOCAL_EMBEDDINGS_ENABLED:
        return _TfidfBackend()
    try:
        return _SentenceTransformerBackend()
    except Exception:
        # Sem internet / pacote não instalado / modelo indisponível -> fallback.
        return _TfidfBackend()


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Retorna um score de 0 a 1 indicando a similaridade semântica entre dois textos."""
    if not text_a or not text_b:
        return 0.0
    return _get_backend().similarity(text_a, text_b)
