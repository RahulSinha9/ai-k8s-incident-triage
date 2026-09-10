# AI Kubernetes Incident Triage 🤖☸️

[![CI](https://github.com/RahulSinha9/ai-k8s-incident-triage/actions/workflows/ci.yml/badge.svg)](https://github.com/RahulSinha9/ai-k8s-incident-triage/actions/workflows/ci.yml)

A portfolio-grade **DevOps + AI-ready Kubernetes incident triage service**. It gathers Kubernetes evidence and converts common failure signals into structured root-cause hypotheses, severity, supporting evidence, and remediation recommendations.

The current version deliberately uses a deterministic diagnosis engine first. This makes the project useful without sending operational logs to an external LLM and creates a safe foundation for adding AI-assisted correlation later.

## Architecture

```text
Kubernetes Cluster
       │
       ▼
 Read-only Collector
       │
       ├── Pod phase
       ├── Container state
       ├── Restart count
       ├── Events
       └── Recent logs
              │
              ▼
       Incident Analyzer
              │
       ┌──────┴────────┐
       │ Rules Engine  │  ← deterministic baseline
       └──────┬────────┘
              ▼
       Triage Report
       ├── Severity
       ├── Category
       ├── Summary
       ├── Evidence
       └── Recommendations
              │
              ▼
      FastAPI / Prometheus
```

## What It Detects

- `CrashLoopBackOff`
- `ImagePullBackOff` / `ErrImagePull`
- `OOMKilled`
- Pending / unscheduled pods
- Excessive restart counts
- Failed or unknown pod states

## Tech Stack

- Python 3.12
- FastAPI
- Kubernetes Python client
- Pydantic
- Prometheus client
- Docker
- Kubernetes RBAC
- GitHub Actions
- Pytest

## Project Structure

```text
.
├── .github/workflows/ci.yml
├── app/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── config.py
│   ├── kubernetes_client.py
│   ├── main.py
│   └── models.py
├── k8s/
│   ├── namespace.yaml
│   ├── serviceaccount.yaml
│   ├── rbac.yaml
│   ├── configmap.yaml
│   └── deployment.yaml
├── tests/
│   ├── test_analyzer.py
│   └── test_api.py
├── .env.example
├── .gitignore
├── Dockerfile
├── Makefile
├── requirements.txt
└── README.md
```

## Local Development

You need Python 3.12+ and a valid kubeconfig if you want to call the triage endpoints.

```bash
git clone https://github.com/RahulSinha9/ai-k8s-incident-triage.git
cd ai-k8s-incident-triage
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application metadata |
| GET | `/health` | Health endpoint |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/triage/{namespace}` | Analyze all pods in a namespace |
| GET | `/api/v1/triage/{namespace}/{pod}` | Analyze one pod |

Example:

```bash
curl http://localhost:8000/api/v1/triage/default
```

Example report:

```json
{
  "namespace": "default",
  "incidents": [
    {
      "namespace": "default",
      "pod": "payments-api-7cddf",
      "severity": "high",
      "category": "crash_loop",
      "summary": "Container is repeatedly crashing and restarting.",
      "evidence": [
        "phase=Running",
        "restart_count=8",
        "reason=CrashLoopBackOff"
      ],
      "recommendations": [
        "Inspect current and previous container logs.",
        "Check application configuration, environment variables and mounted secrets.",
        "Review recent image or deployment changes."
      ]
    }
  ],
  "healthy_pods": 3,
  "analyzed_pods": 4
}
```

## Environment Variables

| Variable | Default | Description |
|---|---:|---|
| `LOG_TAIL_LINES` | `200` | Number of recent log lines collected |
| `RESTART_WARNING_THRESHOLD` | `3` | Restart count that triggers medium severity |
| `RESTART_CRITICAL_THRESHOLD` | `10` | Restart count that triggers high severity |
| `KUBERNETES_CONTEXT` | empty | Optional local kubeconfig context |

## Run Tests

```bash
pytest -q
```

or:

```bash
make test
```

## Docker

```bash
docker build -t ai-k8s-incident-triage:latest .
docker run --rm -p 8000:8000 ai-k8s-incident-triage:latest
```

For actual cluster triage, running the application inside Kubernetes is recommended because the pod receives a ServiceAccount and read-only RBAC permissions.

## Kubernetes Deployment

Build/publish the image and update `k8s/deployment.yaml` if you use a different registry, then:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
```

Check deployment:

```bash
kubectl -n ai-k8s-triage get pods
kubectl -n ai-k8s-triage get svc
```

Access locally:

```bash
kubectl -n ai-k8s-triage port-forward svc/ai-k8s-incident-triage 8000:8000
```

## RBAC

The application uses a ClusterRole because it can triage arbitrary namespaces. Permissions are read-only (`get`, `list`, `watch`) for operational resources such as pods, pod logs, events, nodes, deployments, replica sets, StatefulSets, and DaemonSets.

It does **not** have permission to create, patch, update, or delete workloads.

## Prometheus

Metrics are exposed at:

```text
/metrics
```

The first application metric is `triage_requests_total`, labeled by namespace. More operational metrics can be added as the project grows.

## CI

The GitHub Actions workflow runs on pushes to `main` and pull requests. It:

1. Installs Python dependencies.
2. Runs the Pytest suite.
3. Builds the Docker image to validate the container build.

## Security Design

- Read-only Kubernetes permissions by default.
- Container runs as a non-root user.
- Privilege escalation is disabled.
- Linux capabilities are dropped.
- Root filesystem is read-only in Kubernetes.
- Secrets and `.env` are excluded from Git.
- No generated remediation command is automatically executed.

Before introducing an external LLM, redact secrets, tokens, customer data and credentials from Kubernetes events/logs. Prefer structured model output and require human approval before any mutating remediation.

## AI Roadmap

The next AI layer can consume the sanitized evidence generated by this service rather than receiving unrestricted cluster access. Planned improvements:

- OpenAI-compatible LLM incident summarization
- Cross-pod and deployment-level correlation
- Prometheus alert webhook ingestion
- Loki log correlation
- OpenTelemetry trace correlation
- Slack / Microsoft Teams incident notifications
- Suggested `kubectl` remediation commands
- GitOps remediation pull requests
- Human approval gates for remediation
- Incident history and similarity search

## Troubleshooting

**Kubernetes configuration error locally:** make sure `kubectl get pods` works with your current kubeconfig/context.

**403 from Kubernetes API:** verify the ServiceAccount, ClusterRole, and ClusterRoleBinding are installed.

**ImagePullBackOff for this application:** publish the container image to the registry configured in `k8s/deployment.yaml`, or replace the image reference with your own.

## License

This project is intended for learning, portfolio demonstration, and extension. Add the license that matches your intended distribution model before redistributing it as a packaged product.

---

Built by [RahulSinha9](https://github.com/RahulSinha9) as part of a DevOps + AI engineering portfolio.
