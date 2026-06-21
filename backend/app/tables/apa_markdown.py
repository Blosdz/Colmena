from app.schemas.apa_table import ApaTableRead


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_apa_markdown(table: ApaTableRead) -> str:
    lines: list[str] = []
    if table.table_number is not None:
        lines.append(f"Tabla {table.table_number}")
        lines.append("")
    lines.append(f"*{table.title}*")
    if table.subtitle:
        lines.append("")
        lines.append(table.subtitle)
    lines.append("")
    header = "| " + " | ".join(_escape_cell(column.label) for column in table.columns) + " |"
    separator = "| " + " | ".join("---" for _ in table.columns) + " |"
    lines.extend([header, separator])
    for row in table.rows:
        lines.append("| " + " | ".join(_escape_cell(cell.value) for cell in row.cells) + " |")
    if table.notes:
        lines.append("")
        notes_text = " ".join(note.text for note in table.notes)
        lines.append(f"Nota. {notes_text}")
    return "\n".join(lines)
