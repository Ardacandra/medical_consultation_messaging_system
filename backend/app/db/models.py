from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
import enum
import datetime
from app.db.database import Base

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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
    
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Escalation(Base):
    """The Triage Ticket"""
    __tablename__ = "escalations"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    trigger_message_id = Column(Integer, ForeignKey("messages.id"))
    status = Column(String, default="pending") # pending, resolved
    triage_summary = Column(String) # 3-5 bullet points
