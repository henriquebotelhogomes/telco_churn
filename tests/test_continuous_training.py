import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.db.session import init_db
from churn_prediction.models.continuous_training import ct_pipeline


@pytest.mark.anyio
async def test_continuous_training_pipeline_execution():
    await init_db()

    job_id = await ct_pipeline.start_job(trigger_type="manual_api", auto_promote=False)
    assert job_id.startswith("ct-job-")

    result = await ct_pipeline.execute_job(
        job_id=job_id, trigger_type="manual_api", auto_promote=False
    )

    assert result["job_id"] == job_id
    assert result["status"] in ["SUCCESS", "REJECTED_BY_GATE"]
    assert result["duration_seconds"] > 0
    assert "best_candidate" in result
    assert "details" in result


def test_api_auto_retrain_and_list_jobs():
    with TestClient(app) as client:
        # 1. Dispara retreino via endpoint
        resp = client.post(
            "/api/v1/admin/train/auto-retrain",
            json={"trigger_type": "manual_api", "auto_promote": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "QUEUED"

        # 2. Lista os jobs
        list_resp = client.get("/api/v1/admin/train/jobs")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert "total_jobs" in list_data
        assert "jobs" in list_data
        assert list_data["total_jobs"] >= 1
        assert any(j["job_id"] == data["job_id"] for j in list_data["jobs"])
