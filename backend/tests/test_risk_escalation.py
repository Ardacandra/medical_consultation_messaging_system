import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import RiskAnalysisResult, RiskLevel

client = TestClient(app)

@pytest.mark.asyncio
async def test_high_risk_escalation():
    # Mock the RiskAnalysisService.analyze_risk method
    # We patch the class method to return a specific High Risk result
    
    mock_risk_result = RiskAnalysisResult(
        risk_level=RiskLevel.HIGH,
        reason="Mocked High Risk",
        summary="Mocked Summary"
    )

    with patch("app.services.risk.RiskAnalysisService.analyze_risk", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = mock_risk_result
        
        # Send POST request
        response = client.post(
            "/api/v1/chat/",
            json={"conversation_id": 0, "content": "My chest hurts"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Verify Escalation
        assert "escalation_id" in data
        assert data["message"] == "High risk detected. A nurse has been notified."
        
        # Verify Mock Interaction
        mock_analyze.assert_called_once()
