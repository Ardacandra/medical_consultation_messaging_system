from app.db.models import PatientProfile
from app.services.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class ChatService:
    """
    Service to generate empathetic conversational replies using Gemini.
    """
    def __init__(self):
        self.llm = LLMFactory.create_llm(temperature=0.7) # Higher temp for empathy
        self.parser = StrOutputParser()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are Nightingale, an empathetic medical assistant.\n"
                       "Your goal is to provide supportive, concise responses to the patient.\n"
                       "Context (Patient Profile):\n"
                       "Medications: {medications}\n"
                       "Symptoms: {symptoms}\n\n"
                       "Constraints:\n"
                       "- Do NOT provide medical diagnoses or advice.\n"
                       "- If uncertain, ask clarifying questions.\n"
                       "- Keep responses short (under 50 words)."),
            ("user", "{message}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def generate_reply(self, new_message: str, patient_profile: PatientProfile) -> str:
        """
        Generates a reply based on message and patient profile.
        """
        # Prepare context strings
        meds_str = ", ".join([m['value'] for m in patient_profile.medications]) if patient_profile and patient_profile.medications else "None"
        syms_str = ", ".join([s['value'] for s in patient_profile.symptoms]) if patient_profile and patient_profile.symptoms else "None"
        
        try:
            response = await self.chain.ainvoke({
                "message": new_message,
                "medications": meds_str,
                "symptoms": syms_str
            })
            return response
        except Exception as e:
            print(f"Chat Logic Failed: {e}")
            return "I'm listening. Could you tell me more about how you're feeling?"
