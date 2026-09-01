from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.construct import Construct, ConstructItem
from app.models.question import Question
from app.models.response import Response
from app.models.variable import Variable
from app.repositories.responses import valid_session_ids
from app.repositories.studies import StudyRepository
from app.schemas.datasets import DataDictionary, DataDictionaryEntry, LongDataset, LongDatasetRow, WideDataset


class DatasetService:
    """Fuente única de transformación de datos (harness §19-20).

    Todo análisis futuro (Fase 5+) debe consumir este servicio en lugar de
    repetir consultas de transformación. No persiste un duplicado físico del
    dataset ancho — el pivot se construye dinámicamente (§20).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.study_repo = StudyRepository(session)

    async def _require_study(self, study_id: int):
        study = await self.study_repo.get(study_id)
        if study is None:
            raise NotFoundError(f"Estudio {study_id} no encontrado")
        return study

    async def load_long_dataset(self, study_id: int) -> LongDataset:
        await self._require_study(study_id)

        stmt = (
            select(Response)
            .where(
                Response.study_id == study_id,
                Response.response_session_id.in_(valid_session_ids(study_id)),
            )
            .options(selectinload(Response.question))
            .order_by(Response.response_session_id, Response.question_id)
        )
        responses = list((await self.session.execute(stmt)).scalars().all())

        variable_by_question = await self._variable_code_by_question(study_id)

        # `case_id` es un correlativo asignado en memoria (nunca persistido)
        # en vez del `anonymous_token`/`public_id` de la sesión: evita exponer
        # en exports un identificador estable que permita reidentificar por
        # cruce con logs de invitación (harness §62).
        case_id_by_session: dict[int, int] = {}
        rows = []
        for r in responses:
            case_id = case_id_by_session.setdefault(
                r.response_session_id, len(case_id_by_session) + 1
            )
            rows.append(
                LongDatasetRow(
                    case_id=case_id,
                    question_code=r.question.code,
                    variable_code=variable_by_question.get(r.question_id),
                    raw_code=r.raw_code,
                    numeric_value=float(r.numeric_value) if r.numeric_value is not None else None,
                    text_value=r.text_value,
                    is_missing=r.is_missing,
                )
            )
        return LongDataset(study_id=study_id, rows=rows)

    async def load_wide_dataset(self, study_id: int) -> WideDataset:
        """Pivot dinámico: una fila por respondiente, una columna por ítem (§20)."""
        long_dataset = await self.load_long_dataset(study_id)

        columns: list[str] = []
        seen_columns: set[str] = set()
        by_case: dict[int, dict] = defaultdict(dict)

        for row in long_dataset.rows:
            column = row.variable_code or row.question_code or f"q_{row.question_code}"
            if column not in seen_columns:
                seen_columns.add(column)
                columns.append(column)

            value = row.numeric_value if row.numeric_value is not None else (
                row.text_value if row.text_value is not None else row.raw_code
            )
            by_case[row.case_id]["case_id"] = row.case_id
            by_case[row.case_id][column] = None if row.is_missing else value

        return WideDataset(
            study_id=study_id, columns=["case_id", *columns], rows=list(by_case.values())
        )

    async def _variable_code_by_question(self, study_id: int) -> dict[int, str]:
        study = await self._require_study(study_id)
        stmt = select(Variable.question_id, Variable.code).where(
            Variable.project_id == study.project_id, Variable.question_id.is_not(None)
        )
        return {qid: code for qid, code in (await self.session.execute(stmt)).all()}

    async def load_variable_dictionary(self, study_id: int) -> DataDictionary:
        """Endpoint obligatorio (harness §45)."""
        study = await self._require_study(study_id)

        stmt = select(Variable).where(Variable.project_id == study.project_id)
        variables = list((await self.session.execute(stmt)).scalars().all())

        entries: list[DataDictionaryEntry] = []
        for variable in variables:
            question_code = None
            question_text = None
            constructs: list[str] = []

            if variable.construct_id is not None:
                construct = await self.session.get(Construct, variable.construct_id)
                if construct is not None:
                    constructs = [construct.name]

            if variable.question_id is not None:
                question = await self.session.get(Question, variable.question_id)
                if question is not None:
                    question_code = question.code
                    question_text = question.question_text

                construct_stmt = (
                    select(ConstructItem)
                    .where(ConstructItem.question_id == variable.question_id)
                    .options(selectinload(ConstructItem.construct))
                )
                links = (await self.session.execute(construct_stmt)).scalars().all()
                constructs = [link.construct.name for link in links]

            entries.append(
                DataDictionaryEntry(
                    variable_code=variable.code,
                    label=variable.label or variable.name,
                    data_type=variable.data_type,
                    measurement_level=variable.measurement_level,
                    role=variable.role,
                    source=variable.variable_type,
                    question_code=question_code,
                    question_text=question_text,
                    constructs=constructs,
                )
            )

        return DataDictionary(study_id=study_id, entries=entries)

    # --- Helpers puros reutilizables por analytics (Fase 5+) --------------------

    @staticmethod
    def apply_filters(rows: list[dict], filters: dict[str, object]) -> list[dict]:
        if not filters:
            return rows
        return [row for row in rows if all(row.get(k) == v for k, v in filters.items())]

    @staticmethod
    def apply_privacy_rules(rows: list[dict], group_field: str, min_n: int) -> list[dict]:
        """Suprime grupos con n < min_n (harness §31, aplicado aquí a nivel de dataset).

        La regla formal de privacidad (PrivacyService) se formaliza en Fase 6;
        este helper cubre el caso de uso mínimo de Fase 4: no exponer un
        dataset agregado con celdas por debajo del umbral configurado.
        """
        groups: dict[object, int] = defaultdict(int)
        for row in rows:
            groups[row.get(group_field)] += 1
        return [row for row in rows if groups[row.get(group_field)] >= min_n]
