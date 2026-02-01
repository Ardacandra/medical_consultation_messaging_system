from app.schemas import RiskAnalysisResult, RiskLevel
from app.db.models import Message
from typing import List
import json

class RiskAnalysisService:
    """
    Service to analyze the risk of a user message using an LLM.
    """
    
    async def analyze_risk(self, history: List[Message], new_message_content: str) -> RiskAnalysisResult:
        """
        Analyzes the risk of the new message given the conversation history.
        
        Input: Last 5 messages + New Message.
        Output: RiskAnalysisResult (JSON).
        """
        
        # TODO: Replace with actual LLM call (LangChain/OpenAI) using the prompt:
        # "Analyze risk. Output JSON: {risk: 'HIGH', reason: '...', summary: '...'}"
        
        # Mock Logic for Initial Testing
        content_lower = new_message_content.lower()
        
        if "chest pain" in content_lower or "cardiac" in content_lower or "suicide" in content_lower:
            return RiskAnalysisResult(
                risk_level=RiskLevel.HIGH,
                reason="Detected high-risk keyword (chest pain/cardiac/suicide).",
                summary="Patient reported potential medical emergency."
            )
        
        return RiskAnalysisResult(
            risk_level=RiskLevel.LOW,
            reason="No immediate risk detected.",
            summary="Routine inquiry."
        )
