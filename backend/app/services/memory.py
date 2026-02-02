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
                       "Current Profile Context:\n"
                       "{profile_context}\n\n"
                       "Rules:\n"
                       "1. Normalize names (e.g., 'Advil' -> 'Ibuprofen').\n"
                       "2. If a patient says they STOPPED a med, set status to 'stopped'.\n"
                       "3. CRITICAL: If a patient DENIES a previously mentioned item (from context) or CORRECTS it, output the EXACT existing item value with status 'incorrect'.\n"
                       "4. If a patient says they are taking a med, status is 'active'.\n"
                       "5. If a symptom is resolved, set status to 'resolved'.\n"
                       "6. Chief Complaint: Identify the PRIMARY reason the patient is seeking help (e.g., 'Headache', 'Chest Pain') and extract it as 'chief_complaint'.\n"
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
            # 1. Fetch Profile First
            stmt = select(PatientProfile).where(PatientProfile.patient_id == patient_id)
            db_result = await session.execute(stmt)
            profile = db_result.scalars().first()
            
            if not profile:
                profile = PatientProfile(patient_id=patient_id)
                session.add(profile)
            
            # Prepare Context
            current_meds = ", ".join([m['value'] for m in profile.medications]) if profile.medications else "None"
            current_syms = ", ".join([s['value'] for s in profile.symptoms]) if profile.symptoms else "None"
            profile_context = f"Current Medications: {current_meds}\nCurrent Symptoms: {current_syms}"

            # 2. Invoke LLM with Context
            result = await self.chain.ainvoke({
                "message": message_content,
                "profile_context": profile_context,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            items = result.get("items", [])
            if not items:
                return
            
            # Mutation Helper
            import copy
            def upsert_items(current_list, new_items):
                # FORCE DEEP COPY
                current = copy.deepcopy(list(current_list)) if current_list else []
                utc_now = datetime.utcnow().isoformat()
                
                for item in new_items:
                    # Find existing item (Case-insensitive match)
                    found = False
                    for existing in current:
                        if existing.get('value', '').lower() == item['value'].lower():
                            # Update existing (Mutation)
                            # Handle Negations/Corrections
                            # if item['status'] == 'incorrect':
                            #     # PREVIOUSLY: Remove the item if it was added by mistake or denied
                            #     # NEW: Retain it but mark as incorrect
                            #     pass 
                            
                            # Update Status and timestamps
                            existing['status'] = item['status']
                            existing['provenance_pointer'] = message_id
                            existing['updated_at'] = utc_now
                            
                            if item['status'] == 'stopped':
                                # Add stop timestamp if stopping
                                existing['stopped_at'] = utc_now
                            elif item['status'] == 'active' and 'stopped_at' in existing:
                                # If restarting, clear stopped_at
                                del existing['stopped_at']
                            elif item['status'] == 'incorrect' and 'stopped_at' in existing:
                                # If marking as incorrect, maybe clear stopped_at? Or keep it?
                                # Let's keep it simple: just update validation fields
                                pass

                            found = True
                            break
                    
                    if not found:
                        # Append new (even if incorrect/refuted, we store it as a record of denial)
                        new_record = {
                            "value": item['value'],
                            "status": item['status'],
                            "provenance_pointer": message_id,
                            "updated_at": utc_now
                        }
                        if item['status'] == 'stopped':
                            new_record['stopped_at'] = utc_now
                            
                        current.append(new_record)
                
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
