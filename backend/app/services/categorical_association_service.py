from dataclasses import dataclass

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.form import Form
from app.models.form_question import FormQuestion
from app.models.project_variable import ProjectVariable
from app.schemas.categorical_association import (
    AssociationEffectSizeRead,
    CategoricalAssociationOptionsRead,
    CategoricalAssociationRequest,
    CategoricalAssociationResultRead,
    CategoricalAssociationRunRead,
    CategoricalAssociationTargetInput,
    CategoricalAssociationTargetRead,
    ContingencyTableCellRead,
)
from app.services.normality_service import NormalityService
from app.statistics.categorical_association_engine import (
    build_contingency_table,
    chi_square_test,
    clean_categorical_pair,
    classify_cramers_v,
    classify_phi,
    cramers_v,
    detect_sparse_table,
    expected_count_warnings,
    fisher_exact_test,
    phi_coefficient,
    table_percentages,
)


@dataclass
class ResolvedCategoricalTarget:
    target_type: str
    target_id: str
    label: str
    label_series: pd.Series | None
    value_series: pd.Series | None
    categorical: bool


class CategoricalAssociationService:
    def __init__(self, db: Session):
        self.db = db
        self.normality_service = NormalityService(db)

    def _get_context(
        self,
        form_id: str,
        *,
        include_discarded: bool,
    ) -> tuple[Form, pd.DataFrame, dict]:
        return self.normality_service._get_form_context(form_id, include_discarded=include_discarded)

    def _question_is_categorical(self, question: FormQuestion) -> bool:
        if question.deleted_at is not None:
            return False
        if question.question_type in {"single_choice", "dropdown", "boolean", "likert"}:
            return True
        if question.question_type == "text_short" and question.data_type == "categorical":
            return True
        return False

    def _to_target_read(self, target: ResolvedCategoricalTarget) -> CategoricalAssociationTargetRead:
        return CategoricalAssociationTargetRead(
            target_type=target.target_type,
            target_id=target.target_id,
            label=target.label,
        )

    def resolve_question_categorical_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        question_id: str,
    ) -> ResolvedCategoricalTarget:
        question = self.normality_service._get_question_or_404(form, question_id)
        if not self._question_is_categorical(question):
            return ResolvedCategoricalTarget(
                target_type="question",
                target_id=question.id,
                label=question.label,
                label_series=None,
                value_series=None,
                categorical=False,
            )
        base_name = self.normality_service._get_base_column(question, mapping)
        label_series = dataframe[base_name] if base_name in dataframe.columns else None
        value_name = f"{base_name}__value"
        value_series = dataframe[value_name] if value_name in dataframe.columns else label_series
        return ResolvedCategoricalTarget(
            target_type="question",
            target_id=question.id,
            label=question.label,
            label_series=label_series,
            value_series=value_series,
            categorical=label_series is not None and value_series is not None,
        )

    def resolve_project_variable_categorical_series(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        project_variable_id: str,
    ) -> ResolvedCategoricalTarget:
        variable = self.normality_service._get_project_variable_or_404(form, project_variable_id)
        linked_questions = [
            question
            for question in self.normality_service._active_questions(form)
            if question.project_variable_id == variable.id
        ]
        categorical_questions = [question for question in linked_questions if self._question_is_categorical(question)]
        if len(categorical_questions) != 1:
            return ResolvedCategoricalTarget(
                target_type="project_variable",
                target_id=variable.id,
                label=variable.name,
                label_series=None,
                value_series=None,
                categorical=False,
            )
        question = categorical_questions[0]
        base_name = self.normality_service._get_base_column(question, mapping)
        label_series = dataframe[base_name] if base_name in dataframe.columns else None
        value_name = f"{base_name}__value"
        value_series = dataframe[value_name] if value_name in dataframe.columns else label_series
        return ResolvedCategoricalTarget(
            target_type="project_variable",
            target_id=variable.id,
            label=variable.name,
            label_series=label_series,
            value_series=value_series,
            categorical=label_series is not None and value_series is not None,
        )

    def resolve_categorical_target(
        self,
        form: Form,
        dataframe: pd.DataFrame,
        mapping: dict,
        target: CategoricalAssociationTargetInput,
    ) -> ResolvedCategoricalTarget:
        if target.target_type == "question":
            return self.resolve_question_categorical_series(form, dataframe, mapping, target.target_id)
        if target.target_type == "project_variable":
            return self.resolve_project_variable_categorical_series(form, dataframe, mapping, target.target_id)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported categorical target")

    def choose_auto_method(self, contingency_table: pd.DataFrame) -> tuple[str, list[str]]:
        warnings = ["method_auto_selected"]
        rows, columns = contingency_table.shape
        if rows == 2 and columns == 2:
            chi_result = chi_square_test(contingency_table, alpha=0.05, decimals=6)
            expected = chi_result["expected"]
            if expected is not None and (expected < 5).any():
                warnings.extend(expected_count_warnings(expected))
                return "fisher_exact", list(dict.fromkeys(warnings))
        return "chi_square", warnings

    def _build_effect_size(self, *, method_used: str, contingency_table: pd.DataFrame, chi_result: dict | None, decimals: int) -> AssociationEffectSizeRead | None:
        if chi_result is None or chi_result.get("statistic") is None:
            return None
        rows, columns = contingency_table.shape
        n = int(contingency_table.to_numpy().sum())
        if rows == 2 and columns == 2:
            value = phi_coefficient(float(chi_result["statistic"]), n, decimals=decimals)
            magnitude = classify_phi(value)
            return AssociationEffectSizeRead(
                name="phi",
                value=value,
                magnitude=magnitude,
                interpretation=f"El coeficiente Phi se interpreta como {magnitude} para esta asociacion inicial." if value is not None else "No fue posible calcular Phi con los datos disponibles.",
                warnings=["effect_size_unavailable"] if value is None else [],
            )
        value = cramers_v(float(chi_result["statistic"]), n, rows, columns, decimals=decimals)
        magnitude = classify_cramers_v(value)
        return AssociationEffectSizeRead(
            name="cramers_v",
            value=value,
            magnitude=magnitude,
            interpretation=f"El V de Cramer se interpreta como {magnitude} para esta asociacion inicial." if value is not None else "No fue posible calcular V de Cramer con los datos disponibles.",
            warnings=["effect_size_unavailable"] if value is None else [],
        )

    def build_cells(
        self,
        contingency_table: pd.DataFrame,
        *,
        row_target: ResolvedCategoricalTarget,
        column_target: ResolvedCategoricalTarget,
        expected_table: list[list[float]] | None,
        decimals: int,
    ) -> list[ContingencyTableCellRead]:
        percentages = table_percentages(contingency_table, decimals=decimals)
        expected_lookup: dict[tuple[str, str], float | None] = {}
        if expected_table is not None:
            for row_index, row_value in enumerate(contingency_table.index.tolist()):
                for column_index, column_value in enumerate(contingency_table.columns.tolist()):
                    expected_lookup[(str(row_value), str(column_value))] = round(float(expected_table[row_index][column_index]), decimals)
        cells: list[ContingencyTableCellRead] = []
        for item in percentages:
            cells.append(
                ContingencyTableCellRead(
                    row_label=row_target.label,
                    row_value=item["row_value"],
                    column_label=column_target.label,
                    column_value=item["column_value"],
                    observed=item["observed"],
                    expected=expected_lookup.get((item["row_value"], item["column_value"])),
                    total_percent=item["total_percent"],
                    row_percent=item["row_percent"],
                    column_percent=item["column_percent"],
                )
            )
        return cells

    def build_interpretation(
        self,
        *,
        classification: str,
        method_used: str,
        warnings: list[str],
    ) -> str:
        if classification == "not_applicable":
            return (
                "No fue posible ejecutar una prueba de asociacion categorica con los datos disponibles. "
                "Se recomienda revisar la naturaleza de las variables, la cantidad de categorias y la completitud de la tabla."
            )
        if classification == "not_statistically_significant":
            return (
                "No se identifico una asociacion estadisticamente significativa entre las variables categoricas analizadas, dado que el valor p fue mayor o igual al nivel de significancia establecido. "
                "Por tanto, no se cuenta con evidencia suficiente para afirmar que la distribucion de una variable difiere segun las categorias de la otra en la muestra evaluada."
            )
        base = (
            "Se identifico una asociacion estadisticamente significativa entre las variables categoricas analizadas, dado que el valor p fue menor al nivel de significancia establecido. "
            "Esto indica que la distribucion de frecuencias de una variable varia segun las categorias de la otra. No obstante, este resultado debe interpretarse como asociacion estadistica y no como evidencia de causalidad."
        )
        if "expected_counts_low" in warnings and method_used == "chi_square":
            return base + " El resultado debe interpretarse con cautela debido a la presencia de frecuencias esperadas bajas en una o mas celdas."
        return base

    def build_warnings(
        self,
        *,
        request: CategoricalAssociationRequest,
        form: Form,
        total_n: int,
        valid_n: int,
        missing_n: int,
        row_target: ResolvedCategoricalTarget,
        column_target: ResolvedCategoricalTarget,
        contingency_table: pd.DataFrame,
        initial_warnings: list[str],
        method_used: str,
        chi_result: dict | None,
        fisher_result: dict | None,
        effect_size: AssociationEffectSizeRead | None,
    ) -> list[str]:
        warnings = list(initial_warnings)
        if not request.include_discarded and self.normality_service._has_discarded_responses(form):
            warnings.append("discarded_responses_excluded")
        if request.method != "auto":
            warnings.append("method_forced")
        if missing_n > 0:
            warnings.append("missing_values_present")
        if total_n > 0 and (missing_n / total_n) * 100 >= 20:
            warnings.append("high_missingness")
        if valid_n < 5 and valid_n > 0:
            warnings.append("insufficient_n")
        if not row_target.categorical or not column_target.categorical:
            warnings.append("variable_not_categorical")
        if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
            warnings.append("only_one_category")
        if contingency_table.shape[0] > 20 or contingency_table.shape[1] > 20:
            warnings.append("too_many_categories")
        if detect_sparse_table(contingency_table):
            warnings.append("sparse_table")
        if chi_result is not None:
            warnings.extend(chi_result.get("warnings", []))
        if fisher_result is not None:
            warnings.extend(fisher_result.get("warnings", []))
        if effect_size is not None and effect_size.value is None:
            warnings.append("effect_size_unavailable")
        if method_used == "fisher_exact" and fisher_result is not None and fisher_result.get("odds_ratio") is None:
            warnings.append("odds_ratio_unavailable")
        warnings.append("association_not_causation")
        return list(dict.fromkeys(warnings))

    def store_categorical_association_run(
        self,
        form: Form,
        request: CategoricalAssociationRequest,
        result: CategoricalAssociationResultRead,
    ) -> AnalysisRun:
        analysis_run = AnalysisRun(
            project_id=form.project_id,
            form_id=form.id,
            analysis_type="categorical_association",
            status="completed",
            params_json=request.model_dump(),
            result_json={
                "method_used": result.method_used,
                "valid_n": result.valid_n,
                "row_categories": len(result.row_categories),
                "column_categories": len(result.column_categories),
                "statistic": result.statistic,
                "p_value": result.p_value,
                "classification": result.classification,
            },
        )
        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)
        return analysis_run

    def list_categorical_association_options(self, form_id: str, *, include_discarded: bool = False) -> CategoricalAssociationOptionsRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=include_discarded)
        targets: list[CategoricalAssociationTargetRead] = []
        for question in self.normality_service._active_questions(form):
            resolved = self.resolve_question_categorical_series(form, dataframe, mapping, question.id)
            if resolved.categorical:
                targets.append(self._to_target_read(resolved))
        for variable in self.normality_service._active_project_variables(form):
            resolved = self.resolve_project_variable_categorical_series(form, dataframe, mapping, variable.id)
            if resolved.categorical:
                targets.append(self._to_target_read(resolved))
        seen: set[tuple[str, str]] = set()
        unique_targets: list[CategoricalAssociationTargetRead] = []
        for item in targets:
            key = (item.target_type, item.target_id)
            if key not in seen:
                seen.add(key)
                unique_targets.append(item)
        return CategoricalAssociationOptionsRead(form_id=form.id, categorical_targets=unique_targets)

    def run_categorical_association(self, form_id: str, request: CategoricalAssociationRequest) -> CategoricalAssociationRunRead:
        form, dataframe, mapping = self._get_context(form_id, include_discarded=request.include_discarded)
        row_target = self.resolve_categorical_target(form, dataframe, mapping, request.row)
        column_target = self.resolve_categorical_target(form, dataframe, mapping, request.column)

        if not row_target.categorical or not column_target.categorical:
            result = CategoricalAssociationResultRead(
                form_id=form.id,
                project_id=form.project_id,
                method_requested=request.method,
                method_used="not_applicable",
                alpha=request.alpha,
                row_target=self._to_target_read(row_target),
                column_target=self._to_target_read(column_target),
                total_n=len(dataframe),
                valid_n=0,
                missing_n=len(dataframe),
                row_categories=[],
                column_categories=[],
                observed_table=[],
                expected_table=None,
                cells=[],
                statistic=None,
                degrees_of_freedom=None,
                p_value=None,
                odds_ratio=None,
                classification="not_applicable",
                effect_size=None,
                interpretation="No fue posible ejecutar la asociacion porque una o ambas variables no son categoricas.",
                warnings=["variable_not_categorical", "association_not_causation"],
                required_next_steps=["Seleccionar dos variables categoricas para la tabla de asociacion."],
                assumptions=[],
            )
            analysis_run = self.store_categorical_association_run(form, request, result) if request.store_result else None
            return CategoricalAssociationRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

        paired_frame = clean_categorical_pair(row_target.value_series, column_target.value_series)
        total_n = len(dataframe)
        valid_frame = paired_frame.dropna(subset=["row", "column"], how="any").copy()
        valid_n = len(valid_frame)
        missing_n = total_n - valid_n
        contingency_table = build_contingency_table(valid_frame["row"], valid_frame["column"])

        if valid_n < 3:
            result = CategoricalAssociationResultRead(
                form_id=form.id,
                project_id=form.project_id,
                method_requested=request.method,
                method_used="not_applicable",
                alpha=request.alpha,
                row_target=self._to_target_read(row_target),
                column_target=self._to_target_read(column_target),
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                row_categories=contingency_table.index.astype(str).tolist(),
                column_categories=contingency_table.columns.astype(str).tolist(),
                observed_table=contingency_table.astype(int).values.tolist() if not contingency_table.empty else [],
                expected_table=None,
                cells=[],
                statistic=None,
                degrees_of_freedom=None,
                p_value=None,
                odds_ratio=None,
                classification="not_applicable",
                effect_size=None,
                interpretation="No fue posible ejecutar la asociacion porque la muestra valida es insuficiente para una tabla interpretable.",
                warnings=["insufficient_n", "association_not_causation"],
                required_next_steps=["Aumentar el numero de casos validos antes de ejecutar una prueba inferencial."],
                assumptions=[],
            )
            analysis_run = self.store_categorical_association_run(form, request, result) if request.store_result else None
            return CategoricalAssociationRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

        if contingency_table.empty or contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
            result = CategoricalAssociationResultRead(
                form_id=form.id,
                project_id=form.project_id,
                method_requested=request.method,
                method_used="not_applicable",
                alpha=request.alpha,
                row_target=self._to_target_read(row_target),
                column_target=self._to_target_read(column_target),
                total_n=total_n,
                valid_n=valid_n,
                missing_n=missing_n,
                row_categories=contingency_table.index.astype(str).tolist(),
                column_categories=contingency_table.columns.astype(str).tolist(),
                observed_table=contingency_table.astype(int).values.tolist() if not contingency_table.empty else [],
                expected_table=None,
                cells=[],
                statistic=None,
                degrees_of_freedom=None,
                p_value=None,
                odds_ratio=None,
                classification="not_applicable",
                effect_size=None,
                interpretation="No fue posible ejecutar la asociacion porque no se identificaron al menos dos categorias validas en ambas variables.",
                warnings=["only_one_category", "association_not_causation"],
                required_next_steps=["Verificar la diversidad de categorias y la completitud de la tabla."],
                assumptions=[],
            )
            analysis_run = self.store_categorical_association_run(form, request, result) if request.store_result else None
            return CategoricalAssociationRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)

        initial_warnings: list[str] = []
        method_used = request.method
        if request.method == "auto":
            method_used, auto_warnings = self.choose_auto_method(contingency_table)
            initial_warnings.extend(auto_warnings)

        if request.method == "fisher_exact" and contingency_table.shape != (2, 2):
            initial_warnings.append("fisher_only_for_2x2")
            method_used = "not_applicable"

        chi_result = None
        fisher_result = None
        if method_used == "chi_square":
            chi_result = chi_square_test(contingency_table, alpha=request.alpha, decimals=request.decimals)
        elif method_used == "fisher_exact":
            fisher_result = fisher_exact_test(contingency_table, alpha=request.alpha, decimals=request.decimals)
            chi_result = chi_square_test(contingency_table, alpha=request.alpha, decimals=request.decimals)

        effect_size = self._build_effect_size(
            method_used=method_used,
            contingency_table=contingency_table,
            chi_result=chi_result,
            decimals=request.decimals,
        )

        expected_table = None
        statistic = None
        degrees_of_freedom = None
        p_value = None
        odds_ratio = None
        classification = "not_applicable"
        if method_used == "chi_square" and chi_result is not None:
            expected_table = [[round(float(value), request.decimals) for value in row] for row in chi_result["expected"].tolist()] if chi_result["expected"] is not None else None
            statistic = chi_result["statistic"]
            degrees_of_freedom = chi_result["degrees_of_freedom"]
            p_value = chi_result["p_value"]
            classification = chi_result["classification"]
        elif method_used == "fisher_exact" and fisher_result is not None:
            expected_table = [[round(float(value), request.decimals) for value in row] for row in chi_result["expected"].tolist()] if chi_result is not None and chi_result["expected"] is not None else None
            p_value = fisher_result["p_value"]
            odds_ratio = fisher_result["odds_ratio"]
            classification = fisher_result["classification"]

        warnings = self.build_warnings(
            request=request,
            form=form,
            total_n=total_n,
            valid_n=valid_n,
            missing_n=missing_n,
            row_target=row_target,
            column_target=column_target,
            contingency_table=contingency_table,
            initial_warnings=initial_warnings,
            method_used=method_used,
            chi_result=chi_result,
            fisher_result=fisher_result,
            effect_size=effect_size,
        )

        cells = self.build_cells(
            contingency_table,
            row_target=row_target,
            column_target=column_target,
            expected_table=expected_table,
            decimals=request.decimals,
        )

        result = CategoricalAssociationResultRead(
            form_id=form.id,
            project_id=form.project_id,
            method_requested=request.method,
            method_used=method_used,
            alpha=request.alpha,
            row_target=self._to_target_read(row_target),
            column_target=self._to_target_read(column_target),
            total_n=total_n,
            valid_n=valid_n,
            missing_n=missing_n,
            row_categories=contingency_table.index.astype(str).tolist(),
            column_categories=contingency_table.columns.astype(str).tolist(),
            observed_table=contingency_table.astype(int).values.tolist(),
            expected_table=expected_table,
            cells=cells,
            statistic=statistic,
            degrees_of_freedom=degrees_of_freedom,
            p_value=p_value,
            odds_ratio=odds_ratio,
            classification=classification,
            effect_size=effect_size,
            interpretation=self.build_interpretation(
                classification=classification,
                method_used=method_used,
                warnings=warnings,
            ),
            warnings=warnings,
            required_next_steps=[],
            assumptions=[
                "categorical_variables",
                "independent_observations",
                "valid_contingency_table",
            ],
        )
        analysis_run = self.store_categorical_association_run(form, request, result) if request.store_result else None
        return CategoricalAssociationRunRead(analysis_run_id=analysis_run.id if analysis_run is not None else None, result=result)
