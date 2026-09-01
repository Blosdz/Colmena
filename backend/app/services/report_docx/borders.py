"""Control de bordes, márgenes de celda y reglas horizontales vía OOXML
crudo — python-docx no expone ninguno de estos controles con API pública."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

_EDGES = ("top", "bottom", "left", "right", "insideH", "insideV")


def _border_element(edge: str, *, sz: int, color: str, val: str, space: int = 0):
    element = OxmlElement(f"w:{edge}")
    element.set(qn("w:val"), val)
    element.set(qn("w:sz"), str(sz))
    element.set(qn("w:space"), str(space))
    element.set(qn("w:color"), color)
    return element


def set_cell_border(cell, **edges) -> None:
    """`edges`: cualquiera de top/bottom/left/right, cada uno un dict
    `{"sz": int, "color": "RRGGBB", "val": "single"}` o `None` para no
    tocar ese borde."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    for edge, spec in edges.items():
        if spec is None:
            continue
        existing = borders.find(qn(f"w:{edge}"))
        if existing is not None:
            borders.remove(existing)
        borders.append(_border_element(edge, **spec))


def set_table_borders(table, **edges) -> None:
    for row in table.rows:
        for cell in row.cells:
            set_cell_border(cell, **edges)


def remove_table_borders(table) -> None:
    nil = {"val": "nil", "sz": 0, "color": "auto"}
    for row in table.rows:
        for cell in row.cells:
            set_cell_border(cell, top=nil, bottom=nil, left=nil, right=nil)


def set_cell_margins(cell, *, top: int = 80, start: int = 100, bottom: int = 80, end: int = 100) -> None:
    """Valores en dxa (1 mm ≈ 56.7 dxa). Controla el padding real de la
    celda — Word no permite hacerlo desde la API pública."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:tcMar"))
    if existing is not None:
        tcPr.remove(existing)
    mar = OxmlElement("w:tcMar")
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def add_horizontal_rule(paragraph, *, color: str = "DDA629", size: int = 8) -> None:
    """Regla horizontal como borde inferior del párrafo — nunca una fila de
    guiones de texto."""
    pPr = paragraph._p.get_or_add_pPr()
    existing = pPr.find(qn("w:pBdr"))
    if existing is not None:
        pPr.remove(existing)
    pBdr = OxmlElement("w:pBdr")
    pBdr.append(_border_element("bottom", sz=size, color=color, val="single", space=4))
    pPr.append(pBdr)
