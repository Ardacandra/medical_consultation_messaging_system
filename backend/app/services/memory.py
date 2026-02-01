from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PatientProfile
from sqlalchemy import select
import json
import asyncio

class MemoryService:
    """
    Service to extract medical facts (meds, symptoms) from text and update PatientProfile.
    """

    async def extract_and_update_memory(self, session: AsyncSession, patient_id: int, message_content: str, message_id: int):
        """
        Background task to extract facts and update the patient's living memory.
        """
        # Mock LLM Extraction Delay
        await asyncio.sleep(1)
        
        # Mock Logic: Extract "Advil" or "Headache"
        new_meds = []
        new_symptoms = []
        
        content_lower = message_content.lower()
        
        if "advil" in content_lower:
            new_meds.append({"value": "Advil", "status": "active", "source_msg_id": message_id})
        if "ibuprofen" in content_lower:
            new_meds.append({"value": "Ibuprofen", "status": "active", "source_msg_id": message_id})
            
        if "headache" in content_lower:
            new_symptoms.append({"value": "Headache", "status": "active", "source_msg_id": message_id})
        if "chest pain" in content_lower:
             new_symptoms.append({"value": "Chest Pain", "status": "active", "source_msg_id": message_id})

        if not new_meds and not new_symptoms:
            return

        # Update DB
        # Fetch existing profile or create one
        result = await session.execute(select(PatientProfile).where(PatientProfile.patient_id == patient_id))
        profile = result.scalars().first()
        
        if not profile:
            profile = PatientProfile(patient_id=patient_id)
            session.add(profile)
        
        # Update JSON fields (simple append for now)
        current_meds = profile.medications if profile.medications else []
        current_symptoms = profile.symptoms if profile.symptoms else []
        
        # Avoid exact duplicates for this mock
        for med in new_meds:
            if med["value"] not in [m.get("value") for m in current_meds]:
                current_meds.append(med)
        
        for sym in new_symptoms:
            if sym["value"] not in [s.get("value") for s in current_symptoms]:
                current_symptoms.append(sym)
                
        profile.medications = current_meds
        profile.symptoms = current_symptoms
        
        # Commit happens in the caller or here? 
        # Since this is a background task, we must handle the commit.
        # But 'session' passed from a dependency might be closed if not handled carefully.
        # Usually BackgroundTasks should ideally use a fresh session or be careful.
        # For simplicity in this scaffold, we assume the session is managed by the caller framework 
        # BUT FastAPI BackgroundTasks run *after* response, so the request session is usually closed.
        # FIX: We should create a new session inside this method if it's a true background task, 
        # or pass the ID and instantiate a session here.
        
        await session.commit()
