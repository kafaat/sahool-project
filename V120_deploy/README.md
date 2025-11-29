# V120 — Sangfor SKE Deployment Bundle

This bundle provides Kubernetes + Helm deployment assets tailored for Sangfor HCI / aCloud / SKE.

## Contents
- `helm/` : Helm charts per service + umbrella chart
- `k8s/`  : Raw manifests (namespace, configmaps, secrets, deployments, services, ingress)
- `observability/` : Prometheus + Grafana + Loki (optional)
- `ci-cd/` : GitHub Actions templates for multi-repo build/push/deploy
- `sangfor-notes.md` : Practical notes for Sangfor environments