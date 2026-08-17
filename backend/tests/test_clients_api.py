from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.helpers import wait_for_job


def test_create_list_and_get_404(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    name = f"Cliente {uuid4().hex[:8]}"
    created = client.post("/api/clients", json={"name": name}, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == name
    assert body["meetings_count"] == 0

    listing = client.get("/api/clients", headers=auth_headers)
    assert listing.status_code == 200
    assert any(item["id"] == body["id"] for item in listing.json())

    missing = client.get("/api/clients/999999", headers=auth_headers)
    assert missing.status_code == 404


def test_duplicate_name_conflict(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    name = f"Dup {uuid4().hex[:8]}"
    first = client.post("/api/clients", json={"name": name}, headers=auth_headers)
    assert first.status_code == 201
    other = client.post(
        "/api/clients",
        json={"name": f"Outro {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert other.status_code == 201
    patched = client.patch(
        f"/api/clients/{other.json()['id']}",
        json={"name": name},
        headers=auth_headers,
    )
    assert patched.status_code == 409


def test_clients_are_isolated_per_user(client: TestClient, make_user_headers) -> None:
    headers_a = make_user_headers()
    headers_b = make_user_headers()
    created = client.post(
        "/api/clients",
        json={"name": "Conta exclusiva"},
        headers=headers_a,
    )
    assert created.status_code == 201
    client_id = created.json()["id"]

    listing = client.get("/api/clients", headers=headers_b)
    assert listing.status_code == 200
    assert listing.json() == []

    detail = client.get(f"/api/clients/{client_id}", headers=headers_b)
    assert detail.status_code == 404

    patched = client.patch(
        f"/api/clients/{client_id}",
        json={"notes": "não deveria"},
        headers=headers_b,
    )
    assert patched.status_code == 404


def test_same_client_name_allowed_for_different_users(
    client: TestClient, make_user_headers
) -> None:
    headers_a = make_user_headers()
    headers_b = make_user_headers()
    name = "Mesma Conta"
    first = client.post("/api/clients", json={"name": name}, headers=headers_a)
    second = client.post("/api/clients", json={"name": name}, headers=headers_b)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_get_and_delete_meeting(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Reunião {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "triage": "Triagem da reunião.",
        "selected_agents": ["oportunidade"],
        "final_report": {"conta": "Conta X"},
    }
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)

    uploaded = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("kickoff.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    assert uploaded.status_code == 202, uploaded.text
    job = wait_for_job(client, uploaded.json()["id"], auth_headers)
    meeting_id = job.json()["meeting"]["id"]

    detail = client.get(f"/api/meetings/{meeting_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["triage"] == "Triagem da reunião."
    assert detail.json()["client_id"] == client_id

    deleted = client.delete(f"/api/meetings/{meeting_id}", headers=auth_headers)
    assert deleted.status_code == 204
    missing = client.get(f"/api/meetings/{meeting_id}", headers=auth_headers)
    assert missing.status_code == 404


def test_meeting_isolated_per_user(
    client: TestClient, auth_headers: dict[str, str], make_user_headers, monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Privada {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "triage": "ok",
        "selected_agents": [],
        "final_report": {"conta": "Y"},
    }
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)
    uploaded = client.post(
        "/api/analysis/upload",
        data={"client_id": str(created.json()["id"])},
        files={"file": ("a.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    meeting_id = wait_for_job(client, uploaded.json()["id"], auth_headers).json()["meeting"][
        "id"
    ]
    other = make_user_headers()
    assert client.get(f"/api/meetings/{meeting_id}", headers=other).status_code == 404
    assert client.delete(f"/api/meetings/{meeting_id}", headers=other).status_code == 404
