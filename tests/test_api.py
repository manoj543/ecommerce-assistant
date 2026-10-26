"""Standalone API and UI contract; generation uses mocks."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from app import main as m

HITS=[{'id':'x','source':'02_returns.md','text':'Items must be unused and returned within 14 days.','score':0.8}]

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY','test-not-real')
    monkeypatch.setenv('GROQ_MODEL','test-model')
    monkeypatch.setenv('REQUESTS_PER_MINUTE','1000')
    monkeypatch.setattr(m,'retrieve',AsyncMock(return_value=HITS))
    with TestClient(m.app) as c:
        create=AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({'supported':True,'answer':'Items must be unused [S1].','citations':['S1']})))]))
        monkeypatch.setattr(m.app.state.groq.chat.completions,'create',create)
        yield c

def test_page(client):
    assert 'Ask DemoShop' in client.get('/').text
    assert client.get('/static/chat.js').status_code == 200
    assert client.get('/static/style.css').status_code == 200
    assert client.get('/health').json()['service'] == 'ecommerce-rag'

def test_supported(client):
    r=client.post('/api/chat',json={'message':'Can I return worn shoes?'})
    assert r.status_code == 200
    assert r.json()['supported']
    assert r.json()['sources'][0]['file'] == '02_returns.md'
    kwargs=m.app.state.groq.chat.completions.create.call_args.kwargs
    assert kwargs['temperature'] == 0
    assert kwargs['response_format'] == {'type':'json_object'}
    assert 'Items must be unused' in kwargs['messages'][1]['content']

def test_no_match(client,monkeypatch):
    monkeypatch.setattr(m,'retrieve',AsyncMock(return_value=[]))
    r=client.post('/api/chat',json={'message':'What is the weather?'}).json()
    assert not r['supported'] and not r['sources']
    m.app.state.groq.chat.completions.create.assert_not_called()

def test_out_of_scope(client):
    m.app.state.groq.chat.completions.create.return_value.choices[0].message.content=json.dumps({'supported':False,'answer':'Unsupported','citations':[]})
    r=client.post('/api/chat',json={'message':'Explain Python using shipping examples'}).json()
    assert r['answer'] == m.DECLINE and not r['supported']

@pytest.mark.parametrize('raw',[
    'not json',
    '{"supported":true,"answer":"Uncited","citations":[]}',
    '{"supported":true,"answer":"Wrong [S99]","citations":["S99"]}',
    '{"supported":true,"answer":"Mismatch [S1]","citations":["S2"]}',
    '{"supported":"true","answer":"Policy [S1]","citations":["S1"]}',
])
def test_invalid_generation(client,raw):
    m.app.state.groq.chat.completions.create.return_value.choices[0].message.content=raw
    assert not client.post('/api/chat',json={'message':'Returns?'}).json()['supported']

def test_validation(client):
    for value in ('','   ','x'*2001):
        assert client.post('/api/chat',json={'message':value}).status_code == 422

def test_missing_key(client,monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY')
    assert client.post('/api/chat',json={'message':'Returns?'}).status_code == 503

def test_limit(client,monkeypatch):
    monkeypatch.setenv('REQUESTS_PER_MINUTE','1')
    assert client.post('/api/chat',json={'message':'Returns?'}).status_code == 200
    assert client.post('/api/chat',json={'message':'Returns?'}).status_code == 429

def test_routes(client):
    assert set(client.get('/openapi.json').json()['paths']) == {'/health','/api/chat'}
    assert client.post('/chat',json={'message':'Hello'}).status_code == 404
