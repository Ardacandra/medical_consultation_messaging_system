from pydantic import BaseModel, ConfigDict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RiskAnalysisResult(BaseModel):
    risk_level: RiskLevel
    reason: str
    summary: Optional[str] = None

class MessageCreate(BaseModel):
    content: str
    conversation_id: int

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_type: str
    content: str
    risk_level: RiskLevel
    risk_reason: Optional[str] = None
    confidence: Optional[str] = None
    reason: Optional[str] = None
    citations: Optional[List[str]] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EscalationResponse(BaseModel):
    message: str
    escalation_id: int
    conversation_id: int # Added this
    reason: str

class PatientProfileResponse(BaseModel):
    medications: List[Dict[str, Any]] = []
    symptoms: List[Dict[str, Any]] = []
    allergies: List[Dict[str, Any]] = []
    chief_complaint: List[Dict[str, Any]] = []
    last_updated: datetime

    class Config:
        from_attributes = True
