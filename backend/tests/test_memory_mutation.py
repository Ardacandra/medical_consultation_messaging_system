import pytest
import asyncio
from httpx import AsyncClient

# 2. Test Memory Mutation
@pytest.mark.asyncio
async def test_memory_mutation(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}

    # CLEANUP: Clear profile for patient 1 before starting to avoid legacy data from previous runs
    # (Since we are using a persistent DB for now)
    await client.delete("/api/v1/chat/patient/profile", headers=headers)

    # Turn 1: State valid fact
    payload1 = {
        "conversation_id": 0,
        "content": "I take Advil every day for my headache."
    }
    resp1 = await client.post("/api/v1/chat/", json=payload1, headers=headers)
    assert resp1.status_code == 200
    
    # Wait for background task to process memory (MemoryService extraction runs in background)
    await asyncio.sleep(2) 
    
    # Verify Profile
    prof_resp1 = await client.get("/api/v1/chat/patient/profile", headers=headers)
    assert prof_resp1.status_code == 200
    profile1 = prof_resp1.json()
    
    # Check if Advil is in medications
    meds1 = [m["value"] for m in profile1["medications"]]
    # Note: Exact string match depends on LLM extraction, but "Advil" should be there
    assert any("Advil" in m or "Ibuprofen" in m for m in meds1)
    
    # Turn 2: Negate/Update fact
    # Use same conversation ID if possible, but for simplicity new one works too if profile is global per patient
    payload2 = {
        "conversation_id": resp1.json().get("conversation_id", 0),
        "content": "Actually I stopped taking Advil last week."
    }
    resp2 = await client.post("/api/v1/chat/", json=payload2, headers=headers)
    assert resp2.status_code == 200
    
    await asyncio.sleep(2)
    
    # Verify Profile Update
    prof_resp2 = await client.get("/api/v1/chat/patient/profile", headers=headers)
    profile2 = prof_resp2.json()
    
    # Check status of Advil (or Ibuprofen if normalized)
    meds = profile2["medications"]
    target_meds = [m for m in meds if "Advil" in m["value"] or "Ibuprofen" in m["value"]]
    
    # Check if ANY matching entry has stopped status (handling potential duplicates)
    has_stopped = any(m["status"] in ["stopped", "past", "inactive"] for m in target_meds)
    assert has_stopped, f"Expected stopped status in {target_meds}"
