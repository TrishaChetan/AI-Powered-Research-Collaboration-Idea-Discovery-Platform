"""Users must only be able to see and run AI features on their own papers.

Run from backend/:  pytest tests
Heavy ML dependencies are stubbed, so this needs only fastapi, sqlalchemy,
python-jose and passlib.
"""
import os
import sys
import tempfile
import types

import pytest

# --- stub the ML stack before the app imports it -------------------------------
for name in ("chromadb", "sentence_transformers"):
    if name not in sys.modules:
        stub = types.ModuleType(name)
        stub.SentenceTransformer = object
        stub.PersistentClient = lambda *a, **k: None
        sys.modules[name] = stub

os.chdir(tempfile.mkdtemp())  # keep the test's sqlite file out of the repo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import main, models, rag  # noqa: E402
from app.database import get_db  # noqa: E402

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
models.Base.metadata.create_all(bind=engine)


def _db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = _db
rag.get_embedder = lambda: None
rag.summarize_paper = lambda pid, text: "summary"
main.paper_sample_text = lambda paper: "text"


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def register(client, email):
    r = client.post("/auth/register", json={
        "name": email.split("@")[0], "email": email, "password": "pw123456",
        "education": "", "bio": "", "skills": [], "interests": [],
    })
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def setup(client):
    alice = register(client, "alice@example.com")
    bob = register(client, "bob@example.com")
    alice_id = client.get("/auth/me", headers=alice).json()["id"]
    db = TestSession()
    paper = models.Paper(title="Alice's paper", user_id=alice_id, file_path="x.pdf")
    db.add(paper)
    db.commit()
    pid = paper.id
    db.close()
    return alice, bob, pid


def test_owner_can_read_and_summarize(client, setup):
    alice, _, pid = setup
    assert client.get(f"/papers/{pid}", headers=alice).status_code == 200
    assert client.post(f"/papers/{pid}/summarize", headers=alice).status_code == 200


@pytest.mark.parametrize("method, path", [
    ("get", "/papers/{pid}"),
    ("post", "/papers/{pid}/summarize"),
    ("get", "/papers/{pid}/gaps"),
    ("get", "/papers/{pid}/related"),
])
def test_other_user_gets_404(client, setup, method, path):
    _, bob, pid = setup
    r = getattr(client, method)(path.format(pid=pid), headers=bob)
    assert r.status_code == 404


def test_anonymous_is_rejected(client, setup):
    _, _, pid = setup
    assert client.get(f"/papers/{pid}").status_code == 401
    assert client.get("/users").status_code == 401


def test_compare_rejects_foreign_paper(client, setup):
    _, bob, pid = setup
    r = client.post("/papers/compare", json={"paper_ids": [pid, pid]}, headers=bob)
    assert r.status_code == 404


@pytest.fixture(scope="module")
def idea(client, setup):
    alice, _, pid = setup
    alice_id = client.get("/auth/me", headers=alice).json()["id"]
    db = TestSession()
    i = models.ResearchIdea(title="Alice idea", user_id=alice_id, paper_id=pid, problem="p", approach="a")
    db.add(i)
    db.commit()
    iid = i.id
    db.close()
    return iid


def test_idea_export_requires_owner(client, setup, idea, monkeypatch, tmp_path):
    alice, bob, _ = setup
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    monkeypatch.setattr(main.export_module, "export_idea_to_pdf", lambda d: str(pdf))
    assert client.get(f"/ideas/{idea}/export").status_code == 401
    assert client.get(f"/ideas/{idea}/export", headers=bob).status_code == 404
    r = client.get(f"/ideas/{idea}/export", headers=alice)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")


def test_build_on_others_idea_is_404(client, setup, idea):
    _, bob, _ = setup
    r = client.post(f"/ideas/{idea}/build-on", json={"num_ideas": 1}, headers=bob)
    assert r.status_code == 404


def test_delete_paper_owner_only(client, setup, tmp_path, monkeypatch):
    alice, bob, _ = setup
    alice_id = client.get("/auth/me", headers=alice).json()["id"]
    removed = []
    monkeypatch.setattr(main.rag, "remove_paper", lambda pid: removed.append(pid))
    pdf = os.path.join(main.UPLOAD_DIR, "user_test_delete.pdf")
    os.makedirs(main.UPLOAD_DIR, exist_ok=True)
    open(pdf, "wb").write(b"%PDF")
    db = TestSession()
    paper = models.Paper(title="To delete", user_id=alice_id, file_path=pdf)
    db.add(paper)
    db.commit()
    idea = models.ResearchIdea(title="Child idea", user_id=alice_id, paper_id=paper.id, problem="p", approach="a")
    db.add(idea)
    db.commit()
    pid, iid = paper.id, idea.id
    db.close()

    assert client.delete(f"/papers/{pid}").status_code == 401
    assert client.delete(f"/papers/{pid}", headers=bob).status_code == 404
    assert client.delete(f"/papers/{pid}", headers=alice).status_code == 204
    assert client.get(f"/papers/{pid}", headers=alice).status_code == 404
    assert removed == [pid] and not os.path.exists(pdf)
    db = TestSession()
    kept = db.get(models.ResearchIdea, iid)
    assert kept is not None and kept.paper_id is None   # idea survives, link cleared
    db.close()
