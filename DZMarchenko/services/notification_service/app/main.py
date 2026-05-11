import json

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Notification
from .schemas import NotifyIn, NotifyOut

app = FastAPI(title="notification-service", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/notify", response_model=NotifyOut, status_code=status.HTTP_201_CREATED)
def notify(payload: NotifyIn, db: Session = Depends(get_db)) -> NotifyOut:
    n = Notification(type=payload.type, payload=json.dumps(payload.payload, ensure_ascii=False))
    db.add(n)
    db.commit()
    db.refresh(n)
    return NotifyOut(id=n.id, status=n.status)

