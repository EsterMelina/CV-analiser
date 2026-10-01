"""Local identity extraction from PDF/DOCX CVs."""
from io import BytesIO
import re
import unicodedata
from pydantic import EmailStr, TypeAdapter, ValidationError


UNKNOWN_NAME = "Nome não identificado"


def _fold(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


_LABEL = re.compile(r"^(?:nome(?: completo)?|name|full name)\s*[:：|\t]\s*(.*)$", re.I)
_PARTICLES = {"de", "da", "do", "das", "dos", "e", "van", "von", "del", "di"}
_HEADINGS = {
    "curriculum", "vitae", "curriculo", "resume", "cv", "perfil", "profissional",
    "professional", "profile", "experiencia", "experience", "formacao", "education",
    "contactos", "contacts", "dados", "pessoais", "personal", "informacao", "information",
    "competencias", "skills", "objetivo", "objective", "referencias", "references",
    "engenheiro", "engenheira", "engineer", "developer", "desenvolvedor", "desenvolvedora",
    "gestor", "gestora", "manager", "tecnico", "tecnica", "analista", "analyst",
    "licenciatura", "universidade", "university", "senior", "junior", "software",
    "administrativo", "administrativa", "assistente", "assistant", "consultor", "consultant",
}


def _name(value, *, labelled=False):
    value = " ".join(value.strip().split())
    words = value.split()
    if not 2 <= len(words) <= 8 or len(value) > 255:
        return None
    for word in words:
        folded = _fold(word)
        if not all(c.isalpha() or c in "-’'." for c in word) or not any(c.isalpha() for c in word):
            return None
        if not labelled and folded in _HEADINGS:
            return None
        if not labelled and folded not in _PARTICLES and not word[0].isupper():
            return None
    return value


def name_from_lines(lines):
    lines = [line.strip() for line in lines if line.strip()][:25]
    for i, line in enumerate(lines):
        match = _LABEL.match(line)
        if match or _fold(line) in {"nome", "nome completo", "name", "full name"}:
            value = match.group(1) if match else ""
            if not value and i + 1 < len(lines):
                value = lines[i + 1]
            found = _name(value, labelled=True)
            if found:
                return found
    # Restrict unlabelled guesses to the header, never employers/references below.
    for line in lines[:3]:
        if _fold(line) in {"cv", "curriculum vitae", "curriculo", "curriculo profissional", "resume"}:
            continue
        return _name(line)
    return None


def _document_lines(contents: bytes, extension: str):
    if extension == ".pdf":
        import fitz
        with fitz.open(stream=contents, filetype="pdf") as document:
            lines = [line for page in document for line in page.get_text(sort=True).splitlines()]
    else:
        from docx import Document
        document = Document(BytesIO(contents))
        # Include headers and preserve body order, including tables.
        from docx.oxml.ns import qn
        lines = [p.text for section in document.sections for p in section.header.paragraphs]
        for element in document.element.body:
            if element.tag == qn("w:p"):
                lines.append("".join(t.text or "" for t in element.iter(qn("w:t"))))
            elif element.tag == qn("w:tbl"):
                for row in element.findall(qn("w:tr")):
                    cells = ["".join(t.text or "" for t in cell.iter(qn("w:t")))
                             for cell in row.findall(qn("w:tc"))]
                    lines.append(" | ".join(cells))
    return lines


_EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE)
_EMAIL_TYPE = TypeAdapter(EmailStr)


def email_from_lines(lines):
    addresses = set()
    for line in lines:
        heading = _fold(line.strip()).rstrip(":")
        # Reference contacts belong to other people, not the applicant.
        if re.match(r"^(?:referencias|references|referees)\b", heading):
            break
        for match in _EMAIL.finditer(line):
            try:
                addresses.add(str(_EMAIL_TYPE.validate_python(match.group().lower())))
            except ValidationError:
                continue
    if len(addresses) > 1:
        raise ValueError("O CV contém vários e-mails. Envie uma versão com um único e-mail de contacto do candidato, separando os contactos das referências.")
    return next(iter(addresses), None)


def extract_candidate_identity(contents: bytes, extension: str):
    lines = _document_lines(contents, extension)
    return name_from_lines(lines), email_from_lines(lines)


def extract_candidate_name(contents: bytes, extension: str):
    return name_from_lines(_document_lines(contents, extension))
