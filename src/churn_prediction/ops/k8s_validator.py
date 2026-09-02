from pathlib import Path
from typing import Any


class K8sTopologyValidator:
    """Validador e inspetor declarativo da topologia Kubernetes e KEDA."""

    def __init__(self, k8s_dir: Path | None = None):
        if k8s_dir is None:
            # Tenta resolver o diretório k8s/ a partir da raiz do projeto
            root_cand = Path(__file__).resolve().parent.parent.parent.parent / "k8s"
            if root_cand.exists():
                self.k8s_dir = root_cand
            else:
                self.k8s_dir = Path("k8s")
        else:
            self.k8s_dir = k8s_dir

    def validate_manifests(self) -> dict[str, Any]:
        """Varre e valida a conformidade de todos os manifestos YAML da pasta k8s/."""
        manifest_files = list(self.k8s_dir.glob("*.yaml")) + list(
            (self.k8s_dir / "autoscaling").glob("*.yaml")
        )

        validated_manifests = []
        errors = []

        for mf in manifest_files:
            try:
                content = mf.read_text(encoding="utf-8")
                # Validação básica de presença de apiVersion e kind
                if "apiVersion:" not in content or "kind:" not in content:
                    errors.append(f"Manifesto {mf.name} inválido: ausência de apiVersion ou kind")
                else:
                    validated_manifests.append(
                        {
                            "filename": mf.name,
                            "relative_path": str(mf),
                            "valid": True,
                            "size_bytes": len(content),
                        }
                    )
            except Exception as e:
                errors.append(f"Erro ao ler {mf.name}: {e}")

        return {
            "valid": len(errors) == 0,
            "total_manifests": len(manifest_files),
            "manifests": validated_manifests,
            "errors": errors,
        }

    def get_cluster_topology(self) -> dict[str, Any]:
        """Retorna o estado operacional e topologia simulada do cluster K8s."""
        return {
            "namespace": "retainiq-system",
            "cluster_status": "HEALTHY",
            "environment": "production",
            "deployments": [
                {
                    "name": "retainiq-api",
                    "component": "inference-api",
                    "replicas_current": 2,
                    "replicas_desired": 2,
                    "cpu_limit": "1000m",
                    "memory_limit": "1536Mi",
                    "autoscaling_mode": "HPA",
                    "hpa": {
                        "min_replicas": 2,
                        "max_replicas": 10,
                        "target_cpu_utilization": "70%",
                        "current_cpu_utilization": "28%",
                        "target_memory_utilization": "80%",
                        "current_memory_utilization": "42%",
                    },
                },
                {
                    "name": "retainiq-stream-worker",
                    "component": "stream-processor",
                    "replicas_current": 1,
                    "replicas_desired": 1,
                    "cpu_limit": "500m",
                    "memory_limit": "768Mi",
                    "autoscaling_mode": "KEDA_EVENT_DRIVEN",
                    "keda": {
                        "min_replicas": 1,
                        "max_replicas": 20,
                        "lag_threshold": 500,
                        "current_kafka_lag": 14,
                        "topics_monitored": [
                            "telemetry.network.events",
                            "billing.payment.events",
                        ],
                        "cooldown_period_seconds": 60,
                    },
                },
            ],
            "ingress": {
                "name": "retainiq-ingress",
                "class": "nginx",
                "host": "retainiq.internal.telecom.com",
                "tls_enabled": True,
            },
            "services": [
                {
                    "name": "retainiq-api-service",
                    "type": "ClusterIP",
                    "port": 80,
                    "target_port": 8000,
                }
            ],
        }


# Instância Singleton do Validador K8s
k8s_validator = K8sTopologyValidator()
