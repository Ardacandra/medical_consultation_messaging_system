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
    category: str = Field(description="Must be 'medication', 'symptom', 'allergy', or 'chief_complaint'")
    status: str = Field(description="active, past, stopped, or unknown")

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
            ("system", "You are a medical scribe that extracts structured medical facts.\n"
                       "Extract medications, symptoms, allergies, and chief complaints.\n"
                       "Rules:\n"
                       "1. Normalize names (e.g., 'Advil' -> 'Ibuprofen').\n"
                       "2. If a patient says they STOPPED a med or a symptom ENDED, you MUST extract it and set status to 'stopped' or 'past'.\n"
                       "3. If a patient says they are taking a med, status is 'active'.\n"
                       "Output JSON matching the schema.\n"
                       "{format_instructions}"),
            ("user", "{message}")
        ])
        self.chain = self.prompt | self.llm | self.parser

    async def extract_and_update_memory(self, session: AsyncSession, patient_id: int, message_content: str, message_id: int):
        """
        Extracts entities and updates PatientProfile with proper mutation handling.
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
            
            # Mutation Helper
            import copy
            def upsert_items(current_list, new_items):
                # FORCE DEEP COPY to ensure SQLAlchemy detects change upon reassignment
                # If we modify in place, and the object identity doesn't change enough, 
                # or if the reference is shared weirdly, it might fail.
                # Safest: Create a completely new list of dicts.
                current = copy.deepcopy(list(current_list)) if current_list else []
                utc_now = datetime.utcnow().isoformat()
                
                for item in new_items:
                    # Find existing item (Case-insensitive match)
                    found = False
                    for existing in current:
                        if existing.get('value', '').lower() == item['value'].lower():
                            # Update existing (Mutation)
                            existing['status'] = item['status']
                            existing['source_msg_id'] = message_id
                            existing['updated_at'] = utc_now
                            found = True
                            break
                    
                    if not found:
                        # Append new
                        current.append({
                            "value": item['value'],
                            "status": item['status'],
                            "source_msg_id": message_id,
                            "updated_at": utc_now
                        })
                
                # Flag modified just in case (though assignment should do it)
                return current

            # Split by category and apply upsert
            new_meds = [i for i in items if i['category'] == 'medication']
            new_symptoms = [i for i in items if i['category'] == 'symptom']
            new_allergies = [i for i in items if i['category'] == 'allergy']
            new_cc = [i for i in items if i['category'] == 'chief_complaint']

            if new_meds:
                profile.medications = upsert_items(profile.medications, new_meds)
            if new_symptoms:
                profile.symptoms = upsert_items(profile.symptoms, new_symptoms)
            if new_allergies:
                profile.allergies = upsert_items(profile.allergies, new_allergies)
            if new_cc:
                profile.chief_complaint = upsert_items(profile.chief_complaint, new_cc)
            
            profile.last_updated = datetime.utcnow()
            
            # Explicitly flag modified for SQLAlchemy JSON columns if needed, 
            # though re-assignment usually handles it.
            
            await session.commit()
            
        except Exception as e:
            print(f"Memory Extraction Failed: {e}")
            # Non-critical 
