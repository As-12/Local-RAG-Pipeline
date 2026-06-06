from pathlib import Path
from pypdf import PdfReader
from docx import Document
import markdown
from bs4 import BeautifulSoup


def parse_document(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".md":
        html = markdown.markdown(path.read_text(encoding="utf-8", errors="ignore"))
        return BeautifulSoup(html, "html.parser").get_text("\n")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)

    if suffix == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {suffix}")