"""Validation before persistence and bounded document parsing."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from fastapi import HTTPException

MIME = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def validate_document(contents: bytes, extension: str):
    if extension not in MIME:
        raise HTTPException(400, "Formato não suportado. Utilize PDF ou DOCX")
    if not contents:
        raise HTTPException(422, "Documento vazio")
    try:
        if extension == ".pdf":
            import fitz
            if not contents.startswith(b"%PDF-"):
                raise ValueError("Assinatura inválida")
            with fitz.open(stream=contents, filetype="pdf") as document:
                if document.is_encrypted or not document.page_count or document.page_count > 100:
                    raise ValueError("PDF protegido, vazio ou superior a 100 páginas")
                for page in document:
                    page.get_text()
        else:
            from docx import Document
            with ZipFile(BytesIO(contents)) as archive:
                if sum(info.file_size for info in archive.infolist()) > 50 * 1024 * 1024:
                    raise ValueError("DOCX expandido excede 50MB")
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("Não é DOCX")
            Document(BytesIO(contents))
    except Exception as exc:
        raise HTTPException(422, "Documento corrompido, protegido ou inválido; envie um PDF/DOCX legível") from exc
