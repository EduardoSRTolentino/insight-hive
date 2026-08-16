from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient


def test_upload_persists_meeting(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Upload {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    client_id = created.json()["id"]

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "triage": "Cliente em avaliação.",
        "selected_agents": ["ecossistema_totvs"],
        "final_report": {"conta": "Acme"},
    }
    monkeypatch.setattr("routers.analysis.get_compiled_graph", lambda: fake_graph)

    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["client_id"] == client_id
    assert body["triage"] == "Cliente em avaliação."
    assert body["selected_agents"] == ["ecossistema_totvs"]
    assert body["final_report"]["conta"] == "Acme"
    fake_graph.invoke.assert_called_once()


def test_upload_rejects_oversize(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Big {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    payload = b"x" * 3000
    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("huge.json", payload, "application/json")},
        headers=auth_headers,
    )
    assert response.status_code == 413
