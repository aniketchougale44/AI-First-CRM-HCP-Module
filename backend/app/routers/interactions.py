from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interaction, HCP
from app import schemas

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.name.ilike(payload.hcp_name.strip())).first()
    if not hcp:
        hcp = HCP(name=payload.hcp_name.strip())
        db.add(hcp)
        db.commit()
        db.refresh(hcp)

    interaction = Interaction(
        hcp_id=hcp.id,
        interaction_type=payload.interaction_type,
        date=payload.date,
        time=payload.time,
        attendees=payload.attendees,
        topics_discussed=payload.topics_discussed,
        materials_shared=payload.materials_shared,
        samples_distributed=payload.samples_distributed,
        sentiment=payload.sentiment,
        outcomes=payload.outcomes,
        follow_up_actions=payload.follow_up_actions,
        source=payload.source,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("", response_model=list[schemas.InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.created_at.desc()).all()


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@router.patch("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(
    interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)
):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction
