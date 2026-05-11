from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Chat, ChatMember, Message
from .schemas import (
    AddMemberIn,
    ChatCreateIn,
    ChatOut,
    MessageCreateIn,
    MessageOut,
)
from .security import get_current_user_id
from .settings import settings

app = FastAPI(title="chat-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/", include_in_schema=False)
def ui_index() -> FileResponse:
    return FileResponse(str(WEB_DIR / "index.html"))


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(bind=engine)


def _ensure_member(db: Session, *, chat_id: int, user_id: int) -> None:
    member = db.scalar(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a chat member")


@app.post("/chats", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_chat(
    payload: ChatCreateIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ChatOut:
    chat = Chat(title=payload.title, owner_user_id=user_id)
    db.add(chat)
    db.flush()
    db.add(ChatMember(chat_id=chat.id, user_id=user_id, role="owner"))
    db.commit()
    db.refresh(chat)
    return ChatOut(id=chat.id, title=chat.title, owner_user_id=chat.owner_user_id, created_at=chat.created_at)


@app.get("/chats", response_model=list[ChatOut])
def list_my_chats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[ChatOut]:
    chats = db.scalars(
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.created_at.desc())
    ).all()
    return [
        ChatOut(id=c.id, title=c.title, owner_user_id=c.owner_user_id, created_at=c.created_at) for c in chats
    ]


@app.post("/chats/{chat_id}/members", status_code=status.HTTP_204_NO_CONTENT)
def add_member(
    chat_id: int,
    payload: AddMemberIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # только owner может добавлять участников (упрощенно)
    owner = db.scalar(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id, ChatMember.user_id == user_id, ChatMember.role == "owner"
        )
    )
    if not owner:
        raise HTTPException(status_code=403, detail="Only owner can add members")

    db.add(ChatMember(chat_id=chat_id, user_id=payload.user_id, role=payload.role))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already in chat")


@app.post("/chats/{chat_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(
    chat_id: int,
    payload: MessageCreateIn,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MessageOut:
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _ensure_member(db, chat_id=chat_id, user_id=user_id)

    msg = Message(chat_id=chat_id, author_user_id=user_id, text=payload.text)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # best-effort уведомление (не валим создание сообщения)
    try:
        import httpx

        with httpx.Client(timeout=2.0) as client:
            client.post(
                f"{settings.notification_service_url}/notify",
                json={"type": "message_created", "payload": {"chat_id": chat_id, "message_id": msg.id}},
            )
    except Exception:
        pass

    return MessageOut(
        id=msg.id,
        chat_id=msg.chat_id,
        author_user_id=msg.author_user_id,
        text=msg.text,
        created_at=msg.created_at,
    )


@app.get("/chats/{chat_id}/messages", response_model=list[MessageOut])
def list_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    _ensure_member(db, chat_id=chat_id, user_id=user_id)

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    msgs = db.scalars(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        MessageOut(
            id=m.id,
            chat_id=m.chat_id,
            author_user_id=m.author_user_id,
            text=m.text,
            created_at=m.created_at,
        )
        for m in msgs
    ]


@app.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.author_user_id != user_id:
        raise HTTPException(status_code=403, detail="Only author can delete message")
    db.delete(msg)
    db.commit()

