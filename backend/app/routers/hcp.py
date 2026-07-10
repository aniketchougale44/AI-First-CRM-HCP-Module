from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HCP
from app import schemas

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


@router.get("", response_model=list[schemas.HCPOut])
def list_hcps(q: str = "", db: Session = Depends(get_db)):
    query = db.query(HCP)
    if q:
        query = query.filter(HCP.name.ilike(f"%{q}%"))
    return query.limit(20).all()


@router.post("", response_model=schemas.HCPOut)
def create_hcp(payload: schemas.HCPCreate, db: Session = Depends(get_db)):
    hcp = HCP(**payload.dict())
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp
