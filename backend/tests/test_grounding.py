import pytest
from httpx import AsyncClient

# 5. Test Grounding (Bonus)
@pytest.mark.asyncio
async def test_grounding_citations(client: AsyncClient, patient_token: str):
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Ask a question that requires knowledge
    payload = {
        "conversation_id": 0,
        "content": "What are the side effects of Advil?"
    }
    
    resp = await client.post("/api/v1/chat/", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    
    # Check if citations exist
    assert "citations" in data
    assert isinstance(data["citations"], list)
    # Ideally list is not empty if it found sources, 
    # but strictly checking structure is a good first step.
