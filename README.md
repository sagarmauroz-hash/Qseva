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
Update the image in `k8s/deployment.yaml`, then apply the manifests. The set includes deployment replicas, service/load balancing, HPA, ConfigMap, Secret template, PVC, NetworkPolicy, RBAC, probes and rolling-update settings.

## CI/CD
GitHub Actions runs tests and builds/pushes the container image. Add cluster deployment steps after you know the hackathon cluster's authentication method. Never commit real credentials.

## Serverless
`serverless/function.py` is a platform-neutral event-driven function example. Deploy/adapt it to OpenShift Serverless/Knative or the platform provided by the hackathon.

## Production note
For production, add real authentication/authorization, stricter validation, secret rotation, TLS certificates, managed PostgreSQL, and platform-specific security policies.
