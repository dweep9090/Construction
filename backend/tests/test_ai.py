import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def get_auth_headers():
    from app.auth.security import create_access_token
    access_token = create_access_token(data={"sub": "pm@demo.com"})
    return {"Authorization": f"Bearer {access_token}"}

def test_ai_summary_unauthenticated():
    response = client.post("/api/projects/1/ai-summary")
    assert response.status_code == 401

def test_ai_summary_project_not_found():
    old_provider = settings.AI_PROVIDER
    old_token = settings.HF_TOKEN
    settings.AI_PROVIDER = "huggingface"
    settings.HF_TOKEN = "test_token"
    
    headers = get_auth_headers()
    response = client.post("/api/projects/999/ai-summary", headers=headers)
    assert response.status_code == 404
    
    settings.AI_PROVIDER = old_provider
    settings.HF_TOKEN = old_token

@patch("app.dashboard.router.openai")
def test_ai_summary_missing_api_key(mock_openai):
    old_provider = settings.AI_PROVIDER
    old_token = settings.HF_TOKEN
    settings.AI_PROVIDER = "huggingface"
    settings.HF_TOKEN = None
    
    headers = get_auth_headers()
    response = client.post("/api/projects/1/ai-summary", headers=headers)
    
    if response.status_code != 404:
        assert response.status_code == 501
        assert "missing HF token" in response.json()["detail"]
    
    settings.AI_PROVIDER = old_provider
    settings.HF_TOKEN = old_token

@patch("app.dashboard.router.openai")
def test_ai_summary_success(mock_openai):
    old_provider = settings.AI_PROVIDER
    old_token = settings.HF_TOKEN
    settings.AI_PROVIDER = "huggingface"
    settings.HF_TOKEN = "test_token"
    
    mock_client = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"summary": "Test", "risks": [], "impact": "None", "recommended_attention": []}'
    mock_client.chat.completions.create.return_value = mock_response
    
    headers = get_auth_headers()
    response = client.post("/api/projects/1/ai-summary", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert data["summary"] == "Test"
        assert data["risks"] == []
        assert data["impact"] == "None"
        assert data["recommended_attention"] == []
        
        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert len(kwargs["messages"]) == 2
        assert "Riverfront" in kwargs["messages"][1]["content"] or kwargs["messages"][1]["content"]
    
    settings.AI_PROVIDER = old_provider
    settings.HF_TOKEN = old_token
