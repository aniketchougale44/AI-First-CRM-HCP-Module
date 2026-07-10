import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    hospital = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True, default=gen_uuid)
    hcp_id = Column(String, ForeignKey("hcps.id"), nullable=False)
    interaction_type = Column(String, default="Meeting")
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    attendees = Column(JSON, default=list)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(JSON, default=list)
    samples_distributed = Column(JSON, default=list)
    sentiment = Column(Enum(SentimentEnum), default=SentimentEnum.neutral)
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    ai_suggested_followups = Column(JSON, default=list)
    source = Column(String, default="form")  # "form" or "chat"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, index=True)
    role = Column(String)  # "user" | "assistant" | "tool"
    content = Column(Text)
    tool_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
