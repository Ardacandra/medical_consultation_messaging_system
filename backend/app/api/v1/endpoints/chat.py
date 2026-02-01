from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Message, Escalation, PatientProfile, Conversation, User
from app.schemas import MessageCreate, MessageResponse, EscalationResponse, RiskLevel, PatientProfileResponse
# from app.services.redaction import RedactionService # Deprecated in favor of core.privacy
from app.core.privacy import redact_pii, structured_log
from app.services.risk import RiskAnalysisService
from app.services.memory import MemoryService
from app.services.chat import ChatService
from app.api.deps import get_current_user
from datetime import datetime

router = APIRouter()

# Instantiate Services
risk_service = RiskAnalysisService()
memory_service = MemoryService()
chat_service = ChatService()

@router.post("/", response_model=MessageResponse | EscalationResponse)
async def chat_endpoint(
    msg_in: MessageCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main Chat Interface.
    Flow: Redact -> Save -> Risk -> (Escalate OR Reply + Memory).
    """
    
    # 0. Validate Conversation
    result = await db.execute(select(Conversation).where(Conversation.id == msg_in.conversation_id))
    conversation = result.scalars().first()
    
    if not conversation:
        # Auto-create if ID is 0, assigning to current_user
        if msg_in.conversation_id == 0:
            conversation = Conversation(user_id=current_user.id)
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            msg_in.conversation_id = conversation.id
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify Ownership
    if conversation.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    # Step A: Redaction & Logging
    structured_log("Message Received", {"user_id": current_user.id, "conversation_id": conversation.id})
    content_redacted = redact_pii(msg_in.content)
    
    # Save User Message
    user_msg = Message(
        conversation_id=msg_in.conversation_id,
        sender_type="patient",
        content=msg_in.content, # Encrypted at rest (abstracted)
        content_redacted=content_redacted,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)
    
    # Fetch History for Risk Analysis (Last 5)
    # Simple query
    hist_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == msg_in.conversation_id)
        .order_by(Message.timestamp.desc())
        .limit(5)
    )
    history = hist_result.scalars().all() # Reversed order usually
    
    # Step B: Risk Analysis
    risk_result = await risk_service.analyze_risk(history, content_redacted)
    
    # Update User Message with Risk Metadata
    user_msg.risk_level = risk_result.risk_level
    user_msg.risk_reason = risk_result.reason
    await db.commit()
    
    # If HIGH or MEDIUM RISK -> Stop
    if risk_result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
        # Fetch Profile for Snapshot
        patient_id = conversation.user_id if conversation.user_id else 1
        prof_result = await db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient_id))
        profile = prof_result.scalars().first()
        
        # Serialize Profile
        profile_snapshot = {}
        if profile:
            from fastapi.encoders import jsonable_encoder
            profile_snapshot = jsonable_encoder(PatientProfileResponse.model_validate(profile))

        # Create Escalation
        escalation = Escalation(
            conversation_id=msg_in.conversation_id,
            trigger_message_id=user_msg.id,
            status="pending",
            triage_summary=risk_result.summary or f"{risk_result.risk_level} risk detected via automated analysis.",
            patient_profile_snapshot=profile_snapshot
        )
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)
        
        return EscalationResponse(
            message=f"{risk_result.risk_level} risk detected. A nurse has been notified.",
            escalation_id=escalation.id,
            conversation_id=msg_in.conversation_id,
            reason=risk_result.reason
        )
        
    # Step C: Memory Extraction (Background)
    patient_id = conversation.user_id if conversation.user_id else 1
    background_tasks.add_task(memory_service.extract_and_update_memory, db, patient_id, content_redacted, user_msg.id)

    # Step D: Chat Reply
    # Get Profile
    prof_result = await db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient_id))
    profile = prof_result.scalars().first()
    
    chat_response = await chat_service.generate_reply(content_redacted, profile)
    
    # Map confidence string to score for DB storage (backward compatibility)
    conf_map = {"High": 90, "Medium": 50, "Low": 10}
    db_score = conf_map.get(chat_response.confidence, 0)

    bot_msg = Message(
        conversation_id=msg_in.conversation_id,
        sender_type="ai",
        content=chat_response.content,
        content_redacted=redact_pii(chat_response.content),
        risk_level=RiskLevel.LOW,
        confidence_score=db_score,
        timestamp=datetime.utcnow()
    )
    # Attach transient attributes for API Response (Pydantic schema)
    bot_msg.confidence = chat_response.confidence
    bot_msg.reason = chat_response.reason
    bot_msg.citations = chat_response.citations
    
    db.add(bot_msg)
    await db.commit()
    await db.refresh(bot_msg)
    
    return MessageResponse.model_validate(bot_msg)

@router.get("/{conversation_id}/history", response_model=list[MessageResponse])
async def get_history(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch message history for polling.
    """
    # Security: Verify Conversation Ownership
    query_conv = select(Conversation).where(Conversation.id == conversation_id)
    result_conv = await db.execute(query_conv)
    conversation = result_conv.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    # Fetch Messages
    query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/patient/profile", response_model=PatientProfileResponse)
async def get_patient_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the live patient profile (Living Memory).
    """
    result = await db.execute(select(PatientProfile).where(PatientProfile.patient_id == current_user.id))
    profile = result.scalars().first()
    
    if not profile:
        # Return empty if not exists
        return PatientProfileResponse(
            medications=[], symptoms=[], allergies=[], chief_complaint=[], 
            last_updated=datetime.utcnow()
        )
    
    return profile

@router.delete("/patient/profile", status_code=204)
async def delete_patient_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear the patient profile. Useful for testing or reset.
    """
    result = await db.execute(select(PatientProfile).where(PatientProfile.patient_id == current_user.id))
    profile = result.scalars().first()
    
    if profile:
        await db.delete(profile)
        await db.commit()
    
    return
