from __future__ import annotations

from datetime import datetime

from app.word.docx_placeholders import add_chart_image_or_placeholder, add_future_chart_note
from app.word.docx_styles import apply_body_style, apply_heading_style
from app.word.docx_tables import add_apa_table_to_docx


def _safe_text(value: object, fallback: str = "No especificado") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan"}:
        return fallback
    return text


def build_cover_section(document, *, title: str, subtitle: str | None, project, generated_at: datetime) -> None:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.alignment = 1
    heading.add_run(title).bold = True

    if subtitle:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.alignment = 1
        paragraph.add_run(subtitle)

    for line in [
        f"Proyecto: {_safe_text(project.title)}",
        f"Institucion: {_safe_text(project.institution)}",
        f"Facultad: {_safe_text(project.faculty)}",
        f"Carrera: {_safe_text(project.career)}",
        f"Asesor: {_safe_text(project.advisor_name)}",
        f"Fecha de generacion: {generated_at.strftime('%Y-%m-%d %H:%M')}",
        "Sistema: Colmena",
    ]:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.alignment = 1
        paragraph.add_run(line)


def build_project_section(document, lines: list[str]) -> None:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Datos generales del estudio")
    for line in lines:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(line)


def build_dataset_section(document, lines: list[str]) -> None:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Resumen de la base de datos")
    for line in lines:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(line)


def build_descriptive_section(document, intro: str, tables, start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Resultados descriptivos")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    return table_number


def build_normality_section(document, intro: str, tables, start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Pruebas de normalidad")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    return table_number


def build_scoring_section(document, intro: str, tables, start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Resultados por baremo")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    note = document.add_paragraph()
    apply_body_style(note)
    note.add_run(
        "Los niveles obtenidos corresponden a los rangos configurados para el instrumento y deben interpretarse "
        "de acuerdo con la ficha tecnica y el contexto de aplicacion."
    )
    return table_number


def build_correlation_section(document, intro: str, tables, interpretations: list[str], start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Correlaciones")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    for text in interpretations:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(text)
    return table_number


def build_group_comparison_section(document, intro: str, tables, interpretations: list[str], start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Comparaciones entre grupos")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    for text in interpretations:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(text)
    return table_number


def build_categorical_association_section(document, intro: str, tables, interpretations: list[str], start_table_number: int) -> int:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Asociacion categorica")
    paragraph = document.add_paragraph()
    apply_body_style(paragraph)
    paragraph.add_run(intro)
    table_number = start_table_number
    for table in tables:
        add_apa_table_to_docx(document, table, table_number)
        table_number += 1
    for text in interpretations:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(text)
    return table_number


def build_chart_placeholder_section(document, charts) -> tuple[int, int]:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Graficos sugeridos")
    if not charts:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run("No se identificaron graficos sugeridos para este informe en la fase actual.")
        return 0, 0
    image_count = 0
    placeholder_count = 0
    for index, chart in enumerate(charts, start=1):
        if getattr(chart, "mime_type", None) == "image/png" and getattr(chart, "file_path", None):
            image_count += 1
        else:
            placeholder_count += 1
        add_chart_image_or_placeholder(document, chart, index)
    add_future_chart_note(document)
    return image_count, placeholder_count


def build_conclusion_section(document, conclusions: list[str]) -> None:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Conclusiones estadisticas preliminares")
    for text in conclusions:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(text)


def build_appendix_section(document, lines: list[str]) -> None:
    heading = document.add_paragraph()
    apply_heading_style(heading, 1)
    heading.add_run("Anexo tecnico")
    for line in lines:
        paragraph = document.add_paragraph()
        apply_body_style(paragraph)
        paragraph.add_run(line)
