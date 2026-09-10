from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from app.config import get_settings
from app.models import PodEvidence


class KubernetesEvidenceCollector:
    def __init__(self) -> None:
        settings = get_settings()
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config(context=settings.kubernetes_context)
        self.core = client.CoreV1Api()

    def collect(self, namespace: str, pod_name: str | None = None) -> list[PodEvidence]:
        pods = [self.core.read_namespaced_pod(pod_name, namespace)] if pod_name else self.core.list_namespaced_pod(namespace).items
        return [self._pod_evidence(namespace, pod) for pod in pods]

    def _pod_evidence(self, namespace: str, pod) -> PodEvidence:
        statuses = pod.status.container_statuses or []
        waiting: list[str] = []
        terminated: list[str] = []
        restarts = 0

        for status in statuses:
            restarts += status.restart_count or 0
            if status.state and status.state.waiting and status.state.waiting.reason:
                waiting.append(status.state.waiting.reason)
            if status.state and status.state.terminated and status.state.terminated.reason:
                terminated.append(status.state.terminated.reason)
            if status.last_state and status.last_state.terminated and status.last_state.terminated.reason:
                terminated.append(status.last_state.terminated.reason)

        events = self.core.list_namespaced_event(
            namespace,
            field_selector=f"involvedObject.name={pod.metadata.name}",
        ).items
        event_messages = [f"{event.reason}: {event.message}" for event in events if event.message]

        logs = ""
        if statuses:
            try:
                logs = self.core.read_namespaced_pod_log(
                    pod.metadata.name,
                    namespace,
                    tail_lines=get_settings().log_tail_lines,
                    timestamps=True,
                )
            except client.ApiException as exc:
                logs = f"Unable to read logs: HTTP {exc.status}"

        return PodEvidence(
            namespace=namespace,
            pod=pod.metadata.name,
            phase=pod.status.phase or "Unknown",
            restart_count=restarts,
            waiting_reasons=waiting,
            terminated_reasons=terminated,
            events=event_messages,
            logs=logs,
        )
