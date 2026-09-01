from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationDomainError
from app.models.construct import Construct, ConstructItem
from app.repositories.constructs import ConstructRepository
from app.repositories.instruments import InstrumentRepository
from app.repositories.questions import QuestionRepository
from app.schemas.constructs import (
    ConstructBatchUpdate,
    ConstructCreate,
    ConstructItemCreate,
    ConstructItemUpdate,
    ConstructRead,
    ConstructUpdate,
    StructureVariableCreate,
)
from app.services.audit_service import AuditService
from app.services.instrument_edit_policy import InstrumentEditPolicy


class ConstructService:
    """Editor de dimensiones/subdimensiones (harness §9-10) + asignación de ítems."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConstructRepository(session)
        self.instrument_repo = InstrumentRepository(session)
        self.question_repo = QuestionRepository(session)
        self.audit = AuditService(session)

    async def _load_version_for_policy(self, instrument_version_id: int):
        version = await self.instrument_repo.get_version_with_instrument(instrument_version_id)
        if version is None:
            raise NotFoundError(f"Versión de instrumento {instrument_version_id} no encontrada")
        return version

    async def list_by_version(self, instrument_version_id: int) -> list[Construct]:
        await self._load_version_for_policy(instrument_version_id)
        return await self.repo.list_by_version(instrument_version_id)

    async def list_structure_variables(self, instrument_version_id: int) -> list[Construct]:
        await self._load_version_for_policy(instrument_version_id)
        stmt = (
            select(Construct)
            .where(
                Construct.instrument_version_id == instrument_version_id,
                Construct.construct_type == "VARIABLE",
                Construct.parent_id.is_(None),
            )
            .order_by(Construct.sort_order.asc().nulls_last(), Construct.id.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def _validate_parent(
        self, *, instrument_version_id: int, construct_type: str, parent_id: int | None,
        construct_id: int | None = None,
    ) -> None:
        if construct_type == "VARIABLE":
            if parent_id is not None:
                raise ValidationDomainError("Una variable estructural no puede tener padre.")
            return
        if construct_type not in ("DIMENSION", "SUBDIMENSION"):
            return
        if parent_id is None:
            raise ValidationDomainError(
                "La dimensión debe pertenecer a una variable estructural."
            )
        if construct_id is not None and parent_id == construct_id:
            raise ValidationDomainError("Un nodo no puede ser su propio padre.")
        parent = await self.repo.get(parent_id)
        if parent is None or parent.instrument_version_id != instrument_version_id:
            raise NotFoundError("El nodo padre no pertenece a esta versión.")
        expected_parent_type = "VARIABLE" if construct_type == "DIMENSION" else "DIMENSION"
        if parent.construct_type != expected_parent_type:
            raise ValidationDomainError(
                f"{construct_type} requiere un padre {expected_parent_type}."
            )

    async def create_structure_variable(
        self, instrument_version_id: int, payload: StructureVariableCreate
    ) -> Construct:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)
        construct = Construct(
            instrument_version_id=instrument_version_id,
            parent_id=None,
            code=payload.code,
            name=payload.name,
            construct_type="VARIABLE",
            sort_order=payload.sort_order,
            metadata_={"node_kind": "VARIABLE", "role": payload.role},
        )
        construct = await self.repo.create(construct)
        await self.audit.log(
            action="STRUCTURE_VARIABLE_CREATED",
            entity_type="construct",
            entity_id=construct.id,
            after_data=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return construct

    async def get(self, construct_id: int) -> Construct:
        construct = await self.repo.get(construct_id)
        if construct is None:
            raise NotFoundError(f"Constructo {construct_id} no encontrado")
        return construct

    async def create(self, instrument_version_id: int, payload: ConstructCreate) -> Construct:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        parent_id = payload.parent_id
        await self._validate_parent(
            instrument_version_id=instrument_version_id,
            construct_type=payload.construct_type,
            parent_id=parent_id,
        )

        construct = Construct(
            instrument_version_id=instrument_version_id,
            parent_id=parent_id,
            code=payload.code,
            name=payload.name,
            construct_type=payload.construct_type,
            description=payload.description,
            sort_order=payload.sort_order,
            metadata_=payload.metadata,
        )
        construct = await self.repo.create(construct)
        await self.audit.log(
            action="CONSTRUCT_CREATED",
            entity_type="construct",
            entity_id=construct.id,
            after_data=payload.model_dump(mode="json"),
        )
        await self.session.commit()
        return construct

    async def update(self, construct_id: int, payload: ConstructUpdate) -> Construct:
        construct = await self.get(construct_id)
        version = await self._load_version_for_policy(construct.instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        before = ConstructRead.model_validate(construct).model_dump(mode="json")
        data = payload.model_dump(exclude_unset=True)
        await self._validate_parent(
            instrument_version_id=construct.instrument_version_id,
            construct_type=construct.construct_type,
            parent_id=data.get("parent_id", construct.parent_id),
            construct_id=construct.id,
        )
        if "metadata" in data:
            construct.metadata_ = data.pop("metadata")
        for field, value in data.items():
            setattr(construct, field, value)

        await self.session.flush()
        await self.audit.log(
            action="CONSTRUCT_UPDATED",
            entity_type="construct",
            entity_id=construct.id,
            before_data=before,
            after_data=data,
        )
        await self.session.commit()
        await self.session.refresh(construct)
        return construct

    async def delete(self, construct_id: int) -> None:
        construct = await self.get(construct_id)
        version = await self._load_version_for_policy(construct.instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        await self.audit.log(
            action="CONSTRUCT_DELETED", entity_type="construct", entity_id=construct.id
        )
        await self.repo.delete(construct)
        await self.session.commit()

    async def batch_update(
        self, instrument_version_id: int, payload: ConstructBatchUpdate
    ) -> list[Construct]:
        version = await self._load_version_for_policy(instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        updated: list[Construct] = []
        try:
            for item in payload.items:
                construct = await self.repo.get(item.id)
                if construct is None or construct.instrument_version_id != instrument_version_id:
                    raise NotFoundError(f"Constructo {item.id} no encontrado en esta versión")
                data = item.patch.model_dump(exclude_unset=True)
                await self._validate_parent(
                    instrument_version_id=instrument_version_id,
                    construct_type=construct.construct_type,
                    parent_id=data.get("parent_id", construct.parent_id),
                    construct_id=construct.id,
                )
                if "metadata" in data:
                    construct.metadata_ = data.pop("metadata")
                for field, value in data.items():
                    setattr(construct, field, value)
                updated.append(construct)

            await self.session.flush()
            await self.audit.log(
                action="CONSTRUCT_BATCH_UPDATED",
                entity_type="construct",
                entity_id=None,
                after_data={"ids": [c.id for c in updated]},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for construct in updated:
            await self.session.refresh(construct)
        return updated

    # --- Asignación ítem <-> constructo (harness §10) --------------------------

    async def add_item(
        self, construct_id: int, payload: ConstructItemCreate
    ) -> ConstructItem:
        construct = await self.get(construct_id)
        version = await self._load_version_for_policy(construct.instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        question = await self.question_repo.get(payload.question_id)
        if question is None or question.instrument_version_id != construct.instrument_version_id:
            raise NotFoundError(
                f"Ítem {payload.question_id} no pertenece a esta versión de instrumento"
            )

        item = ConstructItem(
            construct_id=construct_id,
            question_id=payload.question_id,
            weight=payload.weight,
            item_role=payload.item_role,
            scoring_direction=payload.scoring_direction,
            sort_order=payload.sort_order,
        )
        item = await self.repo.add_item(item)
        await self.audit.log(
            action="CONSTRUCT_ITEM_ASSIGNED",
            entity_type="construct_item",
            entity_id=construct_id,
            after_data={"question_id": payload.question_id},
        )
        await self.session.commit()
        return item

    async def update_item(
        self, construct_id: int, question_id: int, payload: ConstructItemUpdate
    ) -> ConstructItem:
        item = await self.repo.get_item(construct_id, question_id)
        if item is None:
            raise NotFoundError("Asignación ítem-constructo no encontrada")

        construct = await self.get(construct_id)
        version = await self._load_version_for_policy(construct.instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(item, field, value)

        await self.session.flush()
        await self.audit.log(
            action="CONSTRUCT_ITEM_UPDATED",
            entity_type="construct_item",
            entity_id=construct_id,
            after_data={"question_id": question_id, **data},
        )
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def remove_item(self, construct_id: int, question_id: int) -> None:
        item = await self.repo.get_item(construct_id, question_id)
        if item is None:
            raise NotFoundError("Asignación ítem-constructo no encontrada")

        construct = await self.get(construct_id)
        version = await self._load_version_for_policy(construct.instrument_version_id)
        await InstrumentEditPolicy.can_edit_construct(self.session, version.instrument, version)

        await self.audit.log(
            action="CONSTRUCT_ITEM_REMOVED",
            entity_type="construct_item",
            entity_id=construct_id,
            after_data={"question_id": question_id},
        )
        await self.repo.delete_item(item)
        await self.session.commit()
