from app.db.models import PatientProfile
from app.services.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatResponse(BaseModel):
    content: str = Field(description="The empathetic response to the patient.")
    confidence: str = Field(description="Confidence in the appropriateness of the response. Value must be 'High', 'Medium', or 'Low'.")
    reason: str = Field(description="Short explanation of why this response was generated and why the confidence level was chosen.")
    citations: List[str] = Field(description="List of sources or provenances (e.g. 'Patient Profile', 'General Medical Knowledge').")

class ChatService:
    """
    Service to generate empathetic conversational replies using Gemini with medical tuning.
    """
    def __init__(self):
        self.llm = LLMFactory.create_llm(temperature=0.3) # Lower temp for more control
        self.parser = JsonOutputParser(pydantic_object=ChatResponse)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are Nightingale, a warm, empathetic, and caring medical assistant.\n"
                       "Your goal is to provide supportive, human-like responses while maintaining safety.\n"
                       "Avoid robotic phrasing like 'I understand' or 'Acknowledged'. Instead, speak naturally like a caring nurse.\n\n"
                       "Context (Patient Profile):\n"
                       "Medications: {medications}\n"
                       "Symptoms: {symptoms}\n\n"
                       "Conversation History (IMPORTANT):\n"
                       "{history}\n\n"
                       "Ground Truth (Clinician Guidance):\n"
                       "Messages in the history labeled 'Verified Nurse' (sender_type: clinician) are GROUND TRUTH. \n"
                       "If clinician guidance conflicts with any other information (including your own prior analysis or patient profile), the clinician guidance ALWAYS wins. \n"
                       "You must follow clinician instructions strictly and cite them if appropriate.\n\n"
                       "Strict Medical Constraints:\n"
                       "1. **Non-Diagnostic**: Do NOT provide medical diagnoses (\"You have X\").\n"
                       "2. **No Med Changes**: Do NOT suggest changing, stopping, or starting medications.\n"
                       "3. **No Treatment Plans**: Provide general info only. Do NOT give specific treatment plans.\n"
                       "4. **No False Reassurance**: Do NOT say \"It's nothing to worry about\" for symptoms like chest pain, high fever, etc.\n"
                       "5. **Consult Clinician Nudge**: If the topic is uncertain, high-stakes, or implies a medical decision, explicitly advise consulting a clinician.\n"
                       "6. **Clarification**: If the patient's statement is vague, ask *one* targeted clarifying question to understand their condition better.\n"
                       "7. **Doctor Recommendation**: If you suggest seeing a doctor, provide a MOCKED recommendation: \"I recommend seeing Dr. Emily Chen (General Practitioner) who has an opening tomorrow at 10:00 AM at City Health Clinic.\"\n\n"
                       "Output Format:\n"
                       "Return valid JSON with 'content', 'confidence' ('High', 'Medium', 'Low'), 'reason', and 'citations'.\n"
                       "{format_instructions}"),
            ("user", "{message}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def generate_reply(self, new_message: str, patient_profile: PatientProfile, history: List[dict]) -> ChatResponse:
        """
        Generates a structured reply based on message, history, and patient profile.
        """
        # Prepare context strings
        meds_str = ", ".join([m['value'] for m in patient_profile.medications]) if patient_profile and patient_profile.medications else "None"
        syms_str = ", ".join([s['value'] for s in patient_profile.symptoms]) if patient_profile and patient_profile.symptoms else "None"
        
        # Format history string
        history_str = ""
        if history:
            # History comes in as objects, need to serialize
            for msg in history:
                if msg.get("sender_type") == "patient":
                    role = "Patient"
                elif msg.get("sender_type") == "clinician":
                    role = "Verified Nurse"
                else:
                    role = "Nightingale"
                
                content = msg.get("content_redacted") or msg.get("content")
                history_str += f"{role}: {content}\n"
        
        try:
            response = await self.chain.ainvoke({
                "message": new_message,
                "history": history_str,
                "medications": meds_str,
                "symptoms": syms_str,
                "format_instructions": self.parser.get_format_instructions()
            })
            return ChatResponse(**response)
        except Exception as e:
            print(f"Chat Logic Failed: {e}")
            # Fallback safe response
            return ChatResponse(
                content="I'm listening, but I'm having trouble processing that right now. Could you tell me more about how you're feeling?",
                confidence="Low",
                reason="System error occurred during response generation.",
                citations=["System Fallback"]
            )
