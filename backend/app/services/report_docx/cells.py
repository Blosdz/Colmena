"""Shading, ancho exacto y alineación vertical de celdas — el ancho de
columna real de Word no es fiable si sólo se confía en `table.autofit`."""

from __future__ import annotations

from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, RGBColor

from .theme import COLMENA


def shade_cell(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    tcPr.append(shd)


def set_cell_vertical_center(cell) -> None:
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _find_or_add(tblPr, tag: str):
    element = tblPr.find(qn(tag))
    if element is None:
        element = OxmlElement(tag)
        tblPr.append(element)
    return element


def set_table_fixed_layout(table, total_width_mm: float) -> None:
    """Ancho fijo real (`w:tblLayout fixed` + `w:tblW`) — sin esto Word
    reparte columnas según el contenido y el layout se rompe entre
    Word/LibreOffice.

    `table.autofit = False` y el constructor de `add_table(width=...)` ya
    insertan sus propios `w:tblLayout`/`w:tblW` — hay que editar esos
    elementos existentes en vez de anexar otros nuevos, o Word/LibreOffice
    reciben dos `w:tblW` contradictorios y el layout colapsa al primero."""
    table.autofit = False
    tblPr = table._tbl.tblPr
    layout = _find_or_add(tblPr, "w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblW = _find_or_add(tblPr, "w:tblW")
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(Mm(total_width_mm).twips)))


def set_column_widths_mm(table, widths_mm: list[float]) -> None:
    """Fija el ancho de cada columna en `gridCol` y en cada celda de cada
    fila — python-docx sólo actualiza la fila que uno toca, no el resto."""
    for idx, width in enumerate(widths_mm):
        if idx < len(table.columns):
            table.columns[idx].width = Mm(width)
    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx < len(widths_mm):
                cell.width = Mm(widths_mm[idx])


def center_table(table) -> None:
    tblPr = table._tbl.tblPr
    jc = _find_or_add(tblPr, "w:jc")
    jc.set(qn("w:val"), "center")


def table_indent(table, twips: int) -> None:
    """Desplaza la tabla horizontalmente (negativo = sangra hacia el borde
    de página, usado por el header/footer para el efecto full-bleed)."""
    tblPr = table._tbl.tblPr
    ind = _find_or_add(tblPr, "w:tblInd")
    ind.set(qn("w:w"), str(twips))
    ind.set(qn("w:type"), "dxa")


def render_status_cell(cell, *, label: str, status: str) -> None:
    """Sólo la celda de estado de un semáforo recibe color de fondo — el
    resto de la fila permanece neutra."""
    palette = {
        "green": COLMENA["green"],
        "red": COLMENA["red"],
        "gold": COLMENA["gold"],
    }
    hex_color = palette.get(status)
    cell.text = label
    if hex_color:
        shade_cell(cell, hex_color)
        for run in cell.paragraphs[0].runs:
            run.font.color.rgb = RGBColor.from_string(COLMENA["white"])
            run.font.bold = True
    set_cell_vertical_center(cell)
