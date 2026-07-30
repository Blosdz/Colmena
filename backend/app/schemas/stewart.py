from pydantic import BaseModel


class StewartPointRead(BaseModel):
    dimension_id: str
    dimension_name: str
    performance_mean: float
    importance_mean: float
    performance_n: int
    importance_n: int


class StewartMatrixRead(BaseModel):
    form_id: str
    instrument_id: str
    instrument_name: str
    points: list[StewartPointRead]
    performance_axis_mean: float | None
    importance_axis_mean: float | None
    warnings: list[str]
