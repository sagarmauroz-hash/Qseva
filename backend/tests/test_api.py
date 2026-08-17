from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    r = client.get('/api/health'); assert r.status_code == 200; assert r.json()['status'] == 'ok'

def test_services():
    r = client.get('/api/services'); assert r.status_code == 200; assert len(r.json()) >= 1

def test_create_token():
    services = client.get('/api/services').json()
    r = client.post('/api/tokens', json={'service_id': services[0]['id']})
    assert r.status_code == 200 and r.json()['token'].startswith('A')
