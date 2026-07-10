from typing import List, Optional
from pydantic import BaseModel


class HCPCreate(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None


class HCPOut(HCPCreate):
    id: str

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    hcp_name: str
    interaction_type: str = "Meeting"
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: List[str] = []
    topics_discussed: Optional[str] = None
    materials_shared: List[str] = []
    samples_distributed: List[str] = []
    sentiment: Optional[str] = "neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    source: str = "form"


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[List[str]] = None
    samples_distributed: Optional[List[str]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionOut(BaseModel):
    id: str
    hcp_id: str
    hcp_name: Optional[str] = None
    interaction_type: str
    date: Optional[str]
    time: Optional[str]
    attendees: List[str]
    topics_discussed: Optional[str]
    materials_shared: List[str]
    samples_distributed: List[str]
    sentiment: str
    outcomes: Optional[str]
    follow_up_actions: Optional[str]
    ai_suggested_followups: List[str]
    source: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[str]
    interaction: Optional[InteractionOut] = None
    ai_suggested_followups: Optional[List[str]] = None