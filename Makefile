run:
	cd backend && uvicorn app.main:app --reload --port 8000

test:
	cd backend && PYTHONPATH=. pytest -q

docker:
	docker compose up --build

k8s:
	kubectl apply -f k8s/
