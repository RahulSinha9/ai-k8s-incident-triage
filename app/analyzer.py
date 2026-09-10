from app.config import get_settings
from app.models import Diagnosis, PodEvidence


def analyze_pod(data: PodEvidence) -> Diagnosis | None:
    settings = get_settings()
    evidence: list[str] = [f"phase={data.phase}", f"restart_count={data.restart_count}"]
    recommendations: list[str] = []

    reasons = set(data.waiting_reasons + data.terminated_reasons)

    if "CrashLoopBackOff" in reasons:
        evidence.append("reason=CrashLoopBackOff")
        recommendations = [
            "Inspect current and previous container logs.",
            "Check application configuration, environment variables and mounted secrets.",
            "Review recent image or deployment changes.",
            "Verify liveness/startup probes are not terminating the application prematurely.",
        ]
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="high", category="crash_loop", summary="Container is repeatedly crashing and restarting.", evidence=evidence, recommendations=recommendations)

    if reasons.intersection({"ImagePullBackOff", "ErrImagePull"}):
        evidence.extend([f"reason={reason}" for reason in sorted(reasons.intersection({"ImagePullBackOff", "ErrImagePull"}))])
        recommendations = [
            "Verify the image repository and tag.",
            "Check imagePullSecrets and registry credentials.",
            "Confirm cluster nodes can reach the container registry.",
        ]
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="high", category="image_pull", summary="Kubernetes cannot pull the container image.", evidence=evidence, recommendations=recommendations)

    if "OOMKilled" in reasons:
        evidence.append("reason=OOMKilled")
        recommendations = [
            "Review container memory usage and memory limits.",
            "Increase the memory limit only after validating expected workload usage.",
            "Investigate memory leaks and unusually large requests.",
        ]
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="critical", category="oom_killed", summary="Container was terminated after exceeding its memory limit.", evidence=evidence, recommendations=recommendations)

    if data.phase == "Pending":
        recommendations = [
            "Inspect pod scheduling events.",
            "Check node capacity, taints/tolerations, affinity and resource requests.",
            "Verify required PVCs are bound.",
        ]
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="medium", category="pending", summary="Pod is not being scheduled or started.", evidence=evidence + data.events[-5:], recommendations=recommendations)

    if data.restart_count >= settings.restart_critical_threshold:
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="high", category="excessive_restarts", summary="Pod has an excessive number of container restarts.", evidence=evidence, recommendations=["Inspect previous logs and termination reasons.", "Review probes and application stability."])

    if data.restart_count >= settings.restart_warning_threshold:
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="medium", category="restarts", summary="Pod restart count is above the warning threshold.", evidence=evidence, recommendations=["Review container logs and recent events."])

    if data.phase in {"Failed", "Unknown"}:
        return Diagnosis(namespace=data.namespace, pod=data.pod, severity="high", category="pod_failure", summary=f"Pod is in {data.phase} phase.", evidence=evidence + data.events[-5:], recommendations=["Inspect pod events and container termination details."])

    return None
