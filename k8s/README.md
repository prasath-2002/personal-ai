# Kubernetes (local kind)

These manifests are for the local `kind` learning environment.

## Build and load images

From the repository root:

```bash
docker build -f Dockerfile.backend -t personal-ai-backend:v2 .

docker build \
  --build-arg NEXT_PUBLIC_API_URL= \
  -t personal-ai-frontend:v2 \
  ./frontend

kind load docker-image personal-ai-backend:v2 --name personal-ai-cluster
kind load docker-image personal-ai-frontend:v2 --name personal-ai-cluster
```

The empty `NEXT_PUBLIC_API_URL` makes browser requests use the same origin, so the Ingress can route frontend and backend traffic through one entry point.

## Deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress.yaml
```

Check:

```bash
kubectl get all -n personal-ai
kubectl get pvc -n personal-ai
kubectl get ingress -n personal-ai
```

The backend intentionally uses one replica because this learning setup stores state in SQLite on a single persistent volume.

No real API keys are committed. To use OpenAI or Groq later, create a `personal-ai-secrets` Kubernetes Secret outside Git and change `LLM_PROVIDER` in the ConfigMap.

The manifests currently use local image names for `kind`. AWS ECR/EKS image references will be added as a later deployment stage.
