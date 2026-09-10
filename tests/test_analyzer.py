from app.analyzer import analyze_pod
from app.models import PodEvidence


def test_crashloopbackoff_is_high_severity():
    evidence = PodEvidence(namespace="default", pod="api-1", phase="Running", restart_count=7, waiting_reasons=["CrashLoopBackOff"])
    result = analyze_pod(evidence)
    assert result is not None
    assert result.category == "crash_loop"
    assert result.severity == "high"


def test_oom_is_critical():
    evidence = PodEvidence(namespace="default", pod="worker-1", phase="Running", restart_count=1, terminated_reasons=["OOMKilled"])
    result = analyze_pod(evidence)
    assert result is not None
    assert result.category == "oom_killed"
    assert result.severity == "critical"


def test_healthy_pod_has_no_incident():
    evidence = PodEvidence(namespace="default", pod="web-1", phase="Running", restart_count=0)
    assert analyze_pod(evidence) is None
