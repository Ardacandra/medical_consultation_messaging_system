from app.db.models import Message, PatientProfile
from typing import List

class ChatService:
    """
    Service to generate empathetic conversational replies using an LLM.
    """
    
    async def generate_reply(self, history: List[Message], profile: PatientProfile, new_message: str) -> str:
        """
        Generates a reply.
        Input: Conversation history + Patient Profile (Context).
        Output: Empathetic response string.
        """
        
        # Mock Logic using Patient Name if available (profile)
        # For now, generic response.
        
        if "chest pain" in new_message.lower():
            # This should have been caught by Risk, but as a fallback:
            return "Please seek emergency medical attention immediately."
            
        return "I understand. Could you tell me more about how you are feeling?"
