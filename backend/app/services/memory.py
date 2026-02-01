from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import PatientProfile
from app.services.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ExtractedItem(BaseModel):
    value: str
    category: str = Field(description="Must be 'medication' or 'symptom' or 'allergy'")
    status: str = Field(description="active, past, or unknown")

class ExtractionResult(BaseModel):
    items: List[ExtractedItem]

class MemoryService:
    """
    Service to extract medical facts from messages using Gemini.
    """
    def __init__(self):
        self.llm = LLMFactory.create_llm(temperature=0.0) 
        self.parser = JsonOutputParser(pydantic_object=ExtractionResult)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a medical scribe. Extract medications, symptoms, and allergies from the text.\n"
                       "Normalize names (e.g., 'Advil' -> 'Ibuprofen').\n"
                       "Output JSON matching the schema.\n"
                       "{format_instructions}"),
            ("user", "{message}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def extract_and_update_memory(self, session: AsyncSession, patient_id: int, message_content: str, message_id: int):
        """
        Extracts entities and updates PatientProfile.
        """
        try:
            result = await self.chain.ainvoke({
                "message": message_content,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            items = result.get("items", [])
            if not items:
                return

            # Fetch Profile
            stmt = select(PatientProfile).where(PatientProfile.patient_id == patient_id)
            db_result = await session.execute(stmt)
            profile = db_result.scalars().first()
            
            if not profile:
                profile = PatientProfile(patient_id=patient_id)
                session.add(profile)
            
            # Helper to append uniques
            def update_list(current_list, new_items):
                current = current_list if current_list else []
                # Simple dedup by value
                existing_values = {i['value'].lower() for i in current}
                
                updated = list(current)
                for item in new_items:
                    if item['value'].lower() not in existing_values:
                        updated.append({
                            "value": item['value'], 
                            "status": item['status'], 
                            "source_msg_id": message_id
                        })
                return updated

            # Split by category
            new_meds = [i for i in items if i['category'] == 'medication']
            new_symptoms = [i for i in items if i['category'] == 'symptom']
            new_allergies = [i for i in items if i['category'] == 'allergy']

            if new_meds:
                profile.medications = update_list(profile.medications, new_meds)
            if new_symptoms:
                profile.symptoms = update_list(profile.symptoms, new_symptoms)
            if new_allergies:
                profile.allergies = update_list(profile.allergies, new_allergies)
            
            profile.last_updated = datetime.utcnow()
            await session.commit()
            
        except Exception as e:
            print(f"Memory Extraction Failed: {e}")
            # Non-critical 
