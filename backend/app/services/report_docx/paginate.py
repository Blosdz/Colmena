"""Control de paginación — evita títulos huérfanos, filas de tabla partidas
y gráficas separadas de su título."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def keep_with_next(paragraph) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:keepNext"))


def prevent_orphan(paragraph) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:widowControl"))


def page_break_before(paragraph) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:pageBreakBefore"))


def keep_table_row_together(row) -> None:
    trPr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    trPr.append(cant_split)
