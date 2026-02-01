from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.database import get_db
from app.db.models import Escalation, Message, RiskLevel, User, Conversation
from app.schemas import MessageResponse, EscalationResponse
from app.api.deps import get_current_clinician
from app.core.privacy import redact_pii
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class EscalationListResponse(BaseModel):
    id: int
    conversation_id: int
    trigger_message_id: int
    status: str
    triage_summary: str
    patient_profile_snapshot: Optional[dict] = {}
    created_at: Optional[str] = None # Helper

    class Config:
        from_attributes = True

class ReplyPayload(BaseModel):
    content: str

@router.get("/", response_model=List[EscalationListResponse])
async def list_escalations(
    status: Optional[str] = "pending",
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(get_current_clinician)
):
    """
    List escalations. Defaults to pending.
    Enforces Clinic Scope: Clinicians only see escalations for patients in their clinic.
    """
    query = select(Escalation)
    if status:
        query = query.where(Escalation.status == status)
    
    # Enforce Clinic Scope
    if current_clinician.clinic_id:
        query = query.join(Conversation, Escalation.conversation_id == Conversation.id)\
                     .join(User, Conversation.user_id == User.id)\
                     .where(User.clinic_id == current_clinician.clinic_id)
    
    result = await db.execute(query)
    escalations = result.scalars().all()
    return escalations

@router.post("/{escalation_id}/reply", response_model=MessageResponse)
async def reply_to_escalation(
    escalation_id: int,
    payload: ReplyPayload,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(get_current_clinician)
):
    """
    Clinician replies to an escalation.
    1. Post message as 'clinician'.
    2. Mark escalation as 'resolved'.
    """
    # 1. Fetch Escalation
    query = select(Escalation).where(Escalation.id == escalation_id)
    
    # Enforce Clinic Scope
    if current_clinician.clinic_id:
        query = query.join(Conversation, Escalation.conversation_id == Conversation.id)\
                     .join(User, Conversation.user_id == User.id)\
                     .where(User.clinic_id == current_clinician.clinic_id)

    result = await db.execute(query)
    escalation = result.scalars().first()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found or access denied")
    
    # 2. Create Message
    content_redacted = redact_pii(payload.content)
    
    clinician_msg = Message(
        conversation_id=escalation.conversation_id,
        sender_type="clinician",
        content=payload.content,
        content_redacted=content_redacted,
        risk_level=RiskLevel.LOW, # Clinician messages arguably don't need risk analysis or are Safe.
        timestamp=datetime.utcnow()
    )
    db.add(clinician_msg)
    
    # 3. Update Escalation Status
    escalation.status = "resolved"
    
    await db.commit()
    await db.refresh(clinician_msg)
    
    return MessageResponse.model_validate(clinician_msg)
