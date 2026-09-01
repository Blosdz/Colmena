"""Configuración física de página — nunca depender de los márgenes por
defecto de Word."""

from __future__ import annotations

from docx import Document

from .theme import PAGE


def configure_page(document: Document):
    section = document.sections[0]
    section.page_width = PAGE["width"]
    section.page_height = PAGE["height"]
    section.top_margin = PAGE["margin_top"]
    section.bottom_margin = PAGE["margin_bottom"]
    section.left_margin = PAGE["margin_left"]
    section.right_margin = PAGE["margin_right"]
    section.header_distance = PAGE["header_distance"]
    section.footer_distance = PAGE["footer_distance"]
    return section
