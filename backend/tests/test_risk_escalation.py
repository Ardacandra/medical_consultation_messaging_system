import pytest
from httpx import AsyncClient

# 1. Test Risk Escalation
@pytest.mark.asyncio
async def test_risk_escalation_high(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Send a high risk message
    payload = {
        "conversation_id": 0, # New conversation
        "content": "I have crushing chest pain and difficulty breathing."
    }
    
    response = await client.post("/api/v1/chat/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Assertions
    # Depending on what the endpoint returns for escalation (EscalationResponse)
    # The schema has 'message' and 'escalation_id'
    
    assert "escalation_id" in data
    assert "risk detected" in data["message"].lower()
    
    # Ideally we check the DB to see if AI *didn't* provide medical advice, 
    # but the API response structure confirming escalation itself implies the AI advice circuit was bypassed or short-circuited.

@pytest.mark.asyncio
async def test_risk_escalation_low(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Send a low risk message
    payload = {
        "conversation_id": 0,
        "content": "I need a refill for my ibuprofen."
    }
    
    response = await client.post("/api/v1/chat/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Expect standard MessageResponse
    assert data["sender_type"] == "ai"
    assert data["risk_level"] == "LOW"
    assert "escalation_id" not in data
