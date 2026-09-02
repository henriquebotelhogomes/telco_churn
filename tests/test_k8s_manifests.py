import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.ops.k8s_validator import K8sTopologyValidator, k8s_validator


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_k8s_manifests_static_validation():
    """Valida a integridade sintática e de segurança de todos os manifestos K8s/KEDA."""
    validator = K8sTopologyValidator()
    res = validator.validate_manifests()

    assert res["valid"] is True
    assert res["total_manifests"] >= 8
    assert len(res["errors"]) == 0

    manifest_names = [m["filename"] for m in res["manifests"]]
    assert "namespace.yaml" in manifest_names
    assert "configmap.yaml" in manifest_names
    assert "secret.yaml" in manifest_names
    assert "api-deployment.yaml" in manifest_names
    assert "api-service.yaml" in manifest_names
    assert "stream-consumer-deployment.yaml" in manifest_names
    assert "ingress.yaml" in manifest_names
    assert "api-hpa.yaml" in manifest_names
    assert "stream-keda-scaledobject.yaml" in manifest_names


def test_k8s_cluster_topology_structure():
    """Valida a estrutura do payload de topologia e metas de autoscaling."""
    topology = k8s_validator.get_cluster_topology()

    assert topology["namespace"] == "retainiq-system"
    assert topology["cluster_status"] == "HEALTHY"
    assert len(topology["deployments"]) == 2

    # Valida HPA
    api_deploy = next(d for d in topology["deployments"] if d["name"] == "retainiq-api")
    assert api_deploy["autoscaling_mode"] == "HPA"
    assert api_deploy["hpa"]["min_replicas"] == 2
    assert api_deploy["hpa"]["max_replicas"] == 10

    # Valida KEDA ScaledObject
    worker_deploy = next(
        d for d in topology["deployments"] if d["name"] == "retainiq-stream-worker"
    )
    assert worker_deploy["autoscaling_mode"] == "KEDA_EVENT_DRIVEN"
    assert worker_deploy["keda"]["min_replicas"] == 1
    assert worker_deploy["keda"]["max_replicas"] == 20
    assert worker_deploy["keda"]["lag_threshold"] == 500


def test_k8s_ops_rest_endpoints(client: TestClient):
    """Testa os endpoints da API para topologia e validação K8s."""
    # 1. GET /api/v1/ops/k8s/topology
    res_topo = client.get("/api/v1/ops/k8s/topology")
    assert res_topo.status_code == 200
    topo_data = res_topo.json()
    assert topo_data["namespace"] == "retainiq-system"
    assert len(topo_data["deployments"]) == 2

    # 2. GET /api/v1/ops/k8s/validate
    res_val = client.get("/api/v1/ops/k8s/validate")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["valid"] is True
    assert val_data["total_manifests"] >= 8
