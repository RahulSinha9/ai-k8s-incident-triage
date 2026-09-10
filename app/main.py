from fastapi import FastAPI, HTTPException
from kubernetes.client.exceptions import ApiException
from prometheus_client import Counter, generate_latest
from starlette.responses import Response

from app.analyzer import analyze_pod
from app.config import get_settings
from app.kubernetes_client import KubernetesEvidenceCollector
from app.models import TriageReport

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
TRIAGE_REQUESTS = Counter("triage_requests_total", "Number of Kubernetes triage requests", ["namespace"])


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")


def run_triage(namespace: str, pod: str | None = None) -> TriageReport:
    TRIAGE_REQUESTS.labels(namespace=namespace).inc()
    try:
        collected = KubernetesEvidenceCollector().collect(namespace, pod)
    except (ApiException, ConfigException) as exc:
        raise HTTPException(status_code=503, detail=f"Kubernetes API unavailable: {exc}") from exc
    incidents = [diagnosis for evidence in collected if (diagnosis := analyze_pod(evidence))]
    return TriageReport(namespace=namespace, incidents=incidents, healthy_pods=len(collected) - len(incidents), analyzed_pods=len(collected))


@app.get("/api/v1/triage/{namespace}", response_model=TriageReport)
def triage_namespace(namespace: str) -> TriageReport:
    return run_triage(namespace)


@app.get("/api/v1/triage/{namespace}/{pod}", response_model=TriageReport)
def triage_pod(namespace: str, pod: str) -> TriageReport:
    return run_triage(namespace, pod)
