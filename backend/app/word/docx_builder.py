from __future__ import annotations

from pathlib import Path

from docx import Document

from app.word.docx_styles import setup_document_defaults


def create_document() -> Document:
    document = Document()
    setup_document_defaults(document)
    return document


def add_page_break(document) -> None:
    document.add_page_break()


def save_document(document, output_path: Path) -> None:
    document.save(output_path)
