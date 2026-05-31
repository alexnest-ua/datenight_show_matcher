"""FastAPI surface: health, profiles, one-shot run, and the SSE stream."""

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["mode"] == "mock"


def test_profiles():
    resp = client.get("/api/profiles")
    assert resp.status_code == 200
    profiles = resp.json()
    assert len(profiles) == 4
    assert all("handle" in p and "display_name" in p for p in profiles)


def test_run_one_shot():
    resp = client.post("/api/run", json={"handle": "@fitness_jane"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["picks"]) == 3
    assert data["mode"] == "mock"


def test_run_rejects_invalid_handle():
    for bad in ["has spaces", "@" + "x" * 40, "<script>", ""]:
        resp = client.post("/api/run", json={"handle": bad})
        assert resp.status_code == 422, bad


def test_stream_rejects_invalid_handle():
    resp = client.get("/api/stream", params={"handle": "x" * 100})
    assert resp.status_code == 422


def test_sse_stream():
    seen: list[str] = []
    with client.stream("GET", "/api/stream?handle=@fitness_jane") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        for line in resp.iter_lines():
            if line.startswith("data:"):
                seen.append(line)
                if "run_completed" in line:
                    break
    assert any("run_started" in s for s in seen)
    assert any("stage_completed" in s for s in seen)
    assert any("run_completed" in s for s in seen)
