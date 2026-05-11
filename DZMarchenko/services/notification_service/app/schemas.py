from pydantic import BaseModel, Field


class NotifyIn(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    payload: dict


class NotifyOut(BaseModel):
    id: int
    status: str

