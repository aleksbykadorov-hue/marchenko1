from datetime import datetime

from pydantic import BaseModel, Field


class ChatCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChatOut(BaseModel):
    id: int
    title: str
    owner_user_id: int
    created_at: datetime


class AddMemberIn(BaseModel):
    user_id: int
    role: str = Field(default="member", max_length=30)


class MessageCreateIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class MessageOut(BaseModel):
    id: int
    chat_id: int
    author_user_id: int
    text: str
    created_at: datetime

