from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.helpers import wait_for_job


def _mock_graph(monkeypatch, **result) -> MagicMock:
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "triage": "Cliente em avaliação.",
        "selected_agents": ["ecossistema_totvs"],
        "final_report": {"conta": "Acme"},
        **result,
    }
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)
    return fake_graph


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

    fake_graph = _mock_graph(monkeypatch)

    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    assert response.status_code == 202, response.text
    job = wait_for_job(client, response.json()["id"], auth_headers)
    body = job.json()
    assert body["status"] == "done"
    meeting = body["meeting"]
    assert meeting["client_id"] == client_id
    assert meeting["triage"] == "Cliente em avaliação."
    assert meeting["selected_agents"] == ["ecossistema_totvs"]
    assert meeting["final_report"]["conta"] == "Acme"
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


def test_upload_rejects_content_length(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Huge {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    payload = b"x" * 25_000
    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("huge.json", payload, "application/json")},
        headers=auth_headers,
    )
    assert response.status_code == 413


def test_upload_rejects_content_length_with_cors_header(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    # Regressão: o middleware de tamanho era registrado depois do CORS, então
    # ficava por fora e a resposta 413 saía sem Access-Control-Allow-Origin —
    # em dev (frontend e API em origens diferentes) o browser bloqueava o
    # corpo e a UI mostrava "não foi possível conectar" em vez do erro real.
    created = client.post(
        "/api/clients",
        json={"name": f"HugeCors {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    payload = b"x" * 25_000
    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("huge.json", payload, "application/json")},
        headers={**auth_headers, "Origin": "http://localhost:5173"},
    )
    assert response.status_code == 413
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_upload_rejects_foreign_client(
    client: TestClient, auth_headers: dict[str, str], make_user_headers, monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Alheio {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    client_id = created.json()["id"]

    fake_graph = MagicMock()
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)

    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=make_user_headers(),
    )
    assert response.status_code == 404
    fake_graph.invoke.assert_not_called()


def test_job_is_isolated_per_user(
    client: TestClient, auth_headers: dict[str, str], make_user_headers, monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Job {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    _mock_graph(monkeypatch)
    uploaded = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    job_id = uploaded.json()["id"]
    foreign = client.get(f"/api/analysis/jobs/{job_id}", headers=make_user_headers())
    assert foreign.status_code == 404
    wait_for_job(client, job_id, auth_headers)


def test_upload_rejects_extensionless_filename(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    # Regressão: sem checar a extensão antes do transcript_cleaner, um nome
    # sem extensão fazia o cleaner sniffar o conteúdo e aceitar como CSV,
    # contornando a allowlist .csv/.json.
    created = client.post(
        "/api/clients",
        json={"name": f"NoExt {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    fake_graph = MagicMock()
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)

    response = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("payload", b"speaker,text\nA,ola\n", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "suportado" in response.json()["detail"]
    fake_graph.invoke.assert_not_called()


def test_upload_fails_job_when_synthesis_card_is_empty(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    # Síntese truncada/inválida vira card todo em "Não identificado" — isso
    # não pode virar uma reunião "done" apresentada como sucesso.
    created = client.post(
        "/api/clients",
        json={"name": f"Empty {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    _mock_graph(monkeypatch, final_report=None)

    uploaded = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    assert uploaded.status_code == 202
    job = wait_for_job(client, uploaded.json()["id"], auth_headers)
    body = job.json()
    assert body["status"] == "failed"
    assert body["meeting"] is None
    assert "síntese" in body["error_detail"].lower()

    client_detail = client.get(f"/api/clients/{client_id}", headers=auth_headers)
    assert client_detail.json()["meetings"] == []


def test_upload_records_ollama_failure(
    client: TestClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    created = client.post(
        "/api/clients",
        json={"name": f"Fail {uuid4().hex[:8]}"},
        headers=auth_headers,
    )
    client_id = created.json()["id"]
    fake_graph = MagicMock()
    fake_graph.invoke.side_effect = ConnectionError("ollama down")
    monkeypatch.setattr("analysis_jobs.get_compiled_graph", lambda: fake_graph)

    uploaded = client.post(
        "/api/analysis/upload",
        data={"client_id": str(client_id)},
        files={"file": ("meeting.json", b'[{"speaker":"A","text":"oi"}]', "application/json")},
        headers=auth_headers,
    )
    assert uploaded.status_code == 202
    job = wait_for_job(client, uploaded.json()["id"], auth_headers)
    body = job.json()
    assert body["status"] == "failed"
    assert body["meeting"] is None
    assert "Ollama" in body["error_detail"]
