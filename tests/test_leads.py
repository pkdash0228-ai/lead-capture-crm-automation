import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import database
from app.main import app

@pytest.fixture
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd)
    monkeypatch.setattr(database, "DB_PATH", Path(path))
    database.init_db()
    with TestClient(app) as test_client:
        yield test_client
    os.unlink(path)

def lead(email="jane@example.com"):
    return {"name":"Jane Smith","email":email,"company":"Acme","message":"Let's talk"}

def test_valid_lead_creation(client):
    response=client.post('/api/leads',json=lead())
    assert response.status_code==200
    assert response.json()['email']=='jane@example.com'
    assert response.json()['status']=='New'

def test_invalid_email(client):
    assert client.post('/api/leads',json=lead('bad-email')).status_code==422

def test_missing_field(client):
    payload=lead(); payload.pop('company')
    assert client.post('/api/leads',json=payload).status_code==422

def test_duplicate_email(client):
    client.post('/api/leads',json=lead())
    assert client.post('/api/leads',json=lead()).status_code==409

def test_case_insensitive_duplicate_detection(client):
    client.post('/api/leads',json=lead('John@gmail.com'))
    response=client.post('/api/leads',json=lead(' JOHN@GMAIL.COM '))
    assert response.status_code==409

def test_csv_import(client):
    content=b'name,email,company,message\nJane,jane@example.com,Acme,Hello\nBob,bob@example.com,Other,Hi\nBad,nope,Co,Oops\n'
    response=client.post('/api/leads/import',files={'file':('leads.csv',content,'text/csv')})
    assert response.status_code==200
    assert response.json()['total_rows']==3
    assert response.json()['successfully_imported']==2
    assert response.json()['invalid_rows']==1

def test_statistics_endpoint(client):
    client.post('/api/leads',json=lead())
    stats=client.get('/api/stats').json()
    assert stats['total_leads']==1 and stats['new_leads']==1 and stats['website_leads']==1


# ----------------------------------------------------------------- chatbot
from app import chat_service

def say(client, sid, history, text):
    history.append({"role": "user", "content": text})
    data = client.post('/api/chat', json={"session_id": sid, "messages": history}).json()
    history.append({"role": "assistant", "content": data["reply"]})
    return data

def test_chat_offline_faq(client, monkeypatch):
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY"): monkeypatch.delenv(k, raising=False)
    data = say(client, "session-faq-1", [], "how does csv import work?")
    assert data["provider"] == "offline" and "CSV" in data["reply"]

def test_chat_offline_lead_capture(client, monkeypatch):
    for k in ("GROQ_API_KEY", "GEMINI_API_KEY"): monkeypatch.delenv(k, raising=False)
    h = []
    say(client, "session-lead-1", h, "I want a demo")
    bad = say(client, "session-lead-1", h, "Jane Smith")
    assert "email" in bad["reply"].lower()
    assert "valid email" in say(client, "session-lead-1", h, "not-an-email")["reply"]
    say(client, "session-lead-1", h, "jane@chat.com"); say(client, "session-lead-1", h, "Acme")
    final = say(client, "session-lead-1", h, "Need a CRM")
    assert final["lead_saved"] is True
    leads = client.get('/api/leads').json()
    assert leads[0]["email"] == "jane@chat.com" and leads[0]["source"] == "Chatbot"
    assert client.get('/api/stats').json()["chatbot_leads"] == 1

def test_chat_llm_tool_call_saves_lead(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test")
    args = '{"name":"Ann","email":"ann@llm.com","company":"Co","message":"Hi"}'
    monkeypatch.setattr(chat_service, "_llm_call", lambda p, m: {"content": None, "tool_calls": [{"function": {"name": "save_lead", "arguments": args}}]})
    data = say(client, "session-llm-1", [], "yes please save it")
    assert data["provider"] == "groq" and data["lead_saved"] is True
    assert client.get('/api/leads').json()[0]["email"] == "ann@llm.com"

def test_chat_llm_failure_falls_back_to_offline(client, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test")
    def boom(p, m): raise RuntimeError("rate limited")
    monkeypatch.setattr(chat_service, "_llm_call", boom)
    assert say(client, "session-fb-1", [], "hello")["provider"] == "offline"

def test_chat_validation(client):
    assert client.post('/api/chat', json={"session_id": "session-bad-1", "messages": [{"role": "assistant", "content": "x"}]}).status_code == 422
