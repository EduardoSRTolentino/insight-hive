from __future__ import annotations

import time

from fastapi.testclient import TestClient


def wait_for_job(
    client: TestClient,
    job_id: int,
    headers: dict[str, str],
    timeout: float = 5.0,
):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/analysis/jobs/{job_id}", headers=headers)
        assert response.status_code == 200, response.text
        if response.json()["status"] in {"done", "failed"}:
            return response
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish")
