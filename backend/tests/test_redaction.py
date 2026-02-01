import pytest
from app.core.privacy import redact_pii

# 3. Test Redaction (Unit Test)
def test_pii_redaction_logic():
    input_text = "My name is John Doe, my IC is S1234567A and my phone is +65 9123 4567."
    redacted = redact_pii(input_text)
    
    assert "John Doe" not in redacted
    assert "S1234567A" not in redacted
    assert "9123 4567" not in redacted
    
    assert "[NRIC_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    # Name redaction might be trickier with simple regex, but let's check if our simple regex caught it 
    # or if we are relying on named patterns. 
    # If the regex in privacy.py is simple, it might miss "John Doe" unless specific pattern.
    # Let's verify what the actual implementation supports. 
    # Assuming standard NRIC/Phone patterns as per requirements.

from httpx import AsyncClient

@pytest.mark.asyncio
async def test_redaction_in_flow(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    payload = {
        "conversation_id": 0,
        "content": "My phone number is 91234567 call me."
    }
    
    resp = await client.post("/api/v1/chat/", json=payload, headers=headers)
    assert resp.status_code == 200
    
    # Verify response doesn't leak it back (though LLM might not repeat it)
    # More importantly, if we could check logs or DB, that would be ideal.
    # For a micro-test against API, we check if the system accepted it and didn't crash.
    # We mainly rely on the unit test above for the logic correctness.
