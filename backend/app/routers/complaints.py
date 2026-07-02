from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Complaint, User
from ..security import current_user

router = APIRouter(prefix="/complaints", tags=["complaints"])


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=3, max_length=2000)
    trip_id: str | None = None


def complaint_dict(complaint: Complaint) -> dict:
    return {
        "id": complaint.id,
        "text": complaint.text,
        "status": complaint.status,
        "trip_id": complaint.trip_id,
        "created_at": complaint.created_at,
        "resolved_at": complaint.resolved_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_complaint(
    body: ComplaintCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    open_count = (
        db.query(Complaint)
        .filter(Complaint.user_id == user.id, Complaint.status == "open")
        .count()
    )
    if open_count >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many open complaints")

    complaint = Complaint(user_id=user.id, trip_id=body.trip_id, text=body.text.strip())
    db.add(complaint)
    db.commit()
    return complaint_dict(complaint)


@router.get("/mine")
def my_complaints(user: User = Depends(current_user), db: Session = Depends(get_db)):
    complaints = (
        db.query(Complaint)
        .filter(Complaint.user_id == user.id)
        .order_by(Complaint.created_at.desc())
        .limit(30)
        .all()
    )
    return [complaint_dict(c) for c in complaints]
