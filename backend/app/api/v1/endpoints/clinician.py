from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from app.db.database import get_db
from app.db.models import User, Message, Conversation, Escalation, PatientProfile
from app.api.deps import get_current_user
from app.schemas import PatientProfileResponse 
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class PatientListItem(BaseModel):
    id: int
    email: str
    last_active: datetime | None
    unread_count: int = 0
    risk_status: str = "normal" # normal, escalated

@router.get("/patients", response_model=List[PatientListItem])
async def get_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve all patients
    # Join with latest message timestamp
    # Check for active escalations
    
    # 1. Get Patients
    q_patients = select(User).where(User.role == "patient")
    res_patients = await db.execute(q_patients)
    patients = res_patients.scalars().all()
    
    patient_list = []
    
    for p in patients:
        # Get last message time
        # This is a bit inefficient (N+1), optimizable with subqueries/joins but fine for prototype
        subq = (
            select(Message.timestamp)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.user_id == p.id)
            .order_by(Message.timestamp.desc())
            .limit(1)
        )
        res_last = await db.execute(subq)
        last_active = res_last.scalars().first() or datetime.min

        # Check for unresolved escalations
        q_esc = (
            select(Escalation)
            .join(Conversation, Conversation.id == Escalation.conversation_id)
            .where(Conversation.user_id == p.id)
            .where(Escalation.status == 'pending')
        )
        res_esc = await db.execute(q_esc)
        active_escalation = res_esc.scalars().first()
        
        status = "escalated" if active_escalation else "normal"

        patient_list.append(PatientListItem(
            id=p.id,
            email=p.email,
            last_active=last_active if last_active != datetime.min else None,
            risk_status=status
        ))
    
    # Sort by last_active desc
    patient_list.sort(key=lambda x: x.last_active or datetime.min, reverse=True)
    
    return patient_list

@router.get("/patient/{patient_id}/profile", response_model=PatientProfileResponse)
async def get_patient_profile_by_id(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific patient's profile (Clinician only).
    """
    if current_user.role != "clinician":
        raise HTTPException(status_code=403, detail="Only clinicians can access this endpoint")

    result = await db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient_id))
    profile = result.scalars().first()
    
    if not profile:
        # Return empty if not exists
        return PatientProfileResponse(
            medications=[], symptoms=[], allergies=[], chief_complaint=[], 
            last_updated=datetime.utcnow()
        )
    
    return profile
