"""Parse one requirement per line from a bounded plain text file."""
import re
from fastapi import HTTPException

MAX_TXT_BYTES = 100 * 1024


def parse_requirements(contents: bytes):
    try:
        encoding = "utf-16" if contents.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        text = contents.decode(encoding)
    except UnicodeError:
        raise HTTPException(422, "Guarde o TXT em UTF-8 ou UTF-16 e tente novamente.") from None
    if any(ord(c) < 32 and c not in "\r\n\t" for c in text):
        raise HTTPException(422, "O ficheiro deve conter apenas texto.")
    values = []
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        value = re.sub(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)", "", line).strip()
        if not value:
            continue
        if len(value) > 4000:
            raise HTTPException(422, f"Linha {number}: limite de 4000 caracteres por requisito.")
        key = " ".join(value.casefold().split())
        if key not in seen:
            seen.add(key)
            values.append(value)
    if not values:
        raise HTTPException(422, "O ficheiro não contém requisitos. Coloque um requisito por linha.")
    if len(values) > 100:
        raise HTTPException(422, "Importe no máximo 100 requisitos por ficheiro.")
    return values
