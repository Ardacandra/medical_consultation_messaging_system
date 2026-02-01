from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.database import get_db
from app.db.models import Escalation, Message, RiskLevel
from app.schemas import MessageResponse, EscalationResponse
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
    created_at: Optional[str] = None # Helper

    class Config:
        from_attributes = True

class ReplyPayload(BaseModel):
    content: str

@router.get("/", response_model=List[EscalationListResponse])
async def list_escalations(
    status: Optional[str] = "pending",
    db: AsyncSession = Depends(get_db)
):
    """
    List escalations. Defaults to pending.
    """
    query = select(Escalation)
    if status:
        query = query.where(Escalation.status == status)
    
    result = await db.execute(query)
    escalations = result.scalars().all()
    return escalations

@router.post("/{escalation_id}/reply", response_model=MessageResponse)
async def reply_to_escalation(
    escalation_id: int,
    payload: ReplyPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Clinician replies to an escalation.
    1. Post message as 'clinician'.
    2. Mark escalation as 'resolved'.
    """
    # 1. Fetch Escalation
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    escalation = result.scalars().first()
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    # 2. Create Message
    # Note: We need a simpler redaction here or reuse service. 
    # For now, simplistic approach: assume clinician data is safe? 
    # Or should we redact clinician messages too? Probably yes for uniformity.
    # We will instantiate RedactionService simpler here or just do identity for speed if not injected.
    # Let's import RedactionService.
    from app.services.redaction import RedactionService
    redactor = RedactionService()
    
    content_redacted = redactor.redact_pii(payload.content)
    
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
