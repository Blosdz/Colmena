import html

from app.schemas.apa_table import ApaTableRead


def render_apa_html(table: ApaTableRead) -> str:
    lines: list[str] = ['<section class="apa-table">']
    if table.table_number is not None:
        lines.append(f"<p><strong>Tabla {table.table_number}</strong></p>")
    lines.append(f"<p><em>{html.escape(table.title)}</em></p>")
    if table.subtitle:
        lines.append(f"<p>{html.escape(table.subtitle)}</p>")
    lines.append('<table>')
    lines.append("<thead>")
    lines.append("<tr>")
    for column in table.columns:
        lines.append(f'<th style="text-align:{column.align}">{html.escape(column.label)}</th>')
    lines.append("</tr>")
    lines.append("</thead>")
    lines.append("<tbody>")
    for row in table.rows:
        lines.append("<tr>")
        for cell in row.cells:
            lines.append(f'<td style="text-align:{cell.align}">{html.escape(cell.value)}</td>')
        lines.append("</tr>")
    lines.append("</tbody>")
    if table.notes:
        lines.append("<tfoot>")
        lines.append("<tr>")
        lines.append(
            f'<td colspan="{len(table.columns)}"><strong>Nota.</strong> {" ".join(html.escape(note.text) for note in table.notes)}</td>'
        )
        lines.append("</tr>")
        lines.append("</tfoot>")
    lines.append("</table>")
    lines.append("</section>")
    return "\n".join(lines)
