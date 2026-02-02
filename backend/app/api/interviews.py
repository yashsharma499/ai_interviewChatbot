from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models import Interview
router = APIRouter()

@router.get("/interviews")
def list_scheduled_interviews():

    db = SessionLocal()

    try:
        interviews = (
            db.query(Interview)
            .filter(Interview.status == "scheduled")
            .order_by(Interview.scheduled_time.asc())
            .all()
        )

        return [
            {
                "id": i.id,
                "candidate_id": i.candidate_id,
                "interviewer_id": i.interviewer_id,
                "scheduled_time": (
                    i.scheduled_time.isoformat()
                    if i.scheduled_time else None
                ),
                "status": i.status
            }
            for i in interviews
        ]

    finally:
        db.close()
