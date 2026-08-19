# QueueLess

QueueLess is a campus digital queue-management MVP designed for a DevOps/Kubernetes hackathon.

## Stack
- Frontend: HTML/CSS/JavaScript
- Backend: Python FastAPI
- Database: PostgreSQL in production; SQLite for quick local testing
- Container: Docker
- CI: GitHub Actions
- Kubernetes/OpenShift: manifests in `k8s/`
- Serverless: example event-driven function in `serverless/`
- Monitoring: Prometheus metrics endpoint; optional Grafana configuration

## Local
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open `http://127.0.0.1:8000`.

## Docker
```bash
docker compose up --build
```
Open `http://localhost:8000`.

## API
- `GET /api/health`
- `GET /api/services`
- `POST /api/tokens`
- `GET /api/queues/{service_id}`
- `POST /api/queues/{service_id}/next`
- `POST /api/tokens/{token_id}/cancel`
- `GET /api/stats`
- `GET /metrics`
- Swagger: `/docs`

## Kubernetes/OpenShift
The OpenShift workflow validates the manifests, applies the PVC and PostgreSQL first, applies the NetworkPolicies, updates the QueueLess image by commit SHA, waits for PostgreSQL, verifies the QueueLess rollout, and prints pod/events diagnostics if rollout fails. Kubernetes DNS egress is explicitly allowed so the `postgres` Service name can resolve.

## CI/CD
GitHub Actions runs tests, builds/pushes both application images, deploys the main application to OpenShift, and verifies the rollout. Keep real cluster credentials in GitHub Actions secrets. The included `k8s/secret.yaml` retains the existing development credentials so it does not unexpectedly rotate the live PostgreSQL password; replace this with an external secret mechanism for production.

## Serverless
`serverless/function.py` is a platform-neutral event-driven function example. Deploy/adapt it to OpenShift Serverless/Knative or the platform provided by the hackathon.

## Production note
For production, add real authentication/authorization, stricter validation, secret rotation, TLS certificates, managed PostgreSQL, and platform-specific security policies.
