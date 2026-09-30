import fitz


def pdf_bytes(text="Curriculo ficticio: experiencia profissional em PHP."):
    with fitz.open() as document:
        page = document.new_page()
        page.insert_text((50, 50), text)
        return document.tobytes(no_new_id=True)
