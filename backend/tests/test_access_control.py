import pytest
from httpx import AsyncClient
from app.core.security import create_access_token

# 4. Test Access Control
@pytest.mark.asyncio
async def test_patient_cannot_access_clinician_queue(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Try to access escalations
    resp = await client.get("/api/v1/escalations/", headers=headers)
    
    # Expect Forbidden
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_clinician_can_access_queue(client: AsyncClient, clinician_token: str):
    headers = {"Authorization": f"Bearer {clinician_token}"}
    
    # Clinician should be able to access escalations
    resp = await client.get("/api/v1/escalations/", headers=headers)
    
    # Expect OK (even if empty)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_conversation_isolation(client: AsyncClient):
    # Token for User A
    token_a = create_access_token(subject="1")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # Token for User B
    token_b = create_access_token(subject="999") # Assuming 999 exists or we mock
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # User A creates convo
    resp = await client.post("/api/v1/chat/", json={"conversation_id": 0, "content": "Hi"}, headers=headers_a)
    assert resp.status_code == 200
    convo_id = resp.json().get("conversation_id")
    
    # User B tries to read User A's convo history
    resp_bad = await client.get(f"/api/v1/chat/{convo_id}/history", headers=headers_b)
    
    # Expect 403 Forbidden (if user exists) or 401 (if user 999 doesn't exist)
    assert resp_bad.status_code in [401, 403, 404]
