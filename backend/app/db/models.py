from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
import enum
import datetime
from app.db.database import Base

class RiskLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="patient") # patient, clinician
    is_active = Column(Boolean, default=True)
    clinic_id = Column(String, nullable=True) # For RBAC scoping

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender_type = Column(String) # "patient", "ai", "clinician"
    content = Column(String) # Encrypted at rest
    content_redacted = Column(String) # Safe for logs
    
    # Provenance & Risk Metadata
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    risk_reason = Column(String, nullable=True)
    confidence_score = Column(Integer, nullable=True) # 0-100
    
    # Voice Readiness
    audio_transcript_id = Column(String, nullable=True) # ID from voice provider
    audio_url = Column(String, nullable=True) # S3/Blob URL

    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

Conversation.messages = relationship("Message", back_populates="conversation")

class PatientProfile(Base):
    """The 'Living Memory' - updates live"""
    __tablename__ = "patient_profiles"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    
    # Structured Facts (Stored as JSON with provenance)
    # Example structure: 
    # { "value": "Advil", "status": "active", "source_msg_id": 12 }
    medications = Column(JSON, default=list) 
    symptoms = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    chief_complaint = Column(JSON, default=list)
    
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Escalation(Base):
    """The Triage Ticket"""
    __tablename__ = "escalations"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    trigger_message_id = Column(Integer, ForeignKey("messages.id"))
    status = Column(String, default="pending") # pending, resolved
    triage_summary = Column(String) # 3-5 bullet points
    patient_profile_snapshot = Column(JSON, nullable=True) # Snapshot at time of escalation
