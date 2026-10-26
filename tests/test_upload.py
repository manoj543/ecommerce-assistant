import json
from types import SimpleNamespace
import pytest
from app import upload_vectors as u
from qdrant_client import models


def test_cloud_required(monkeypatch, tmp_path):
    monkeypatch.delenv("QDRANT_URL",raising=False)
    with pytest.raises(ValueError,match="QDRANT_URL"):
        u.upload(tmp_path / "unused.jsonl")


def test_existing_vector_upload(monkeypatch,tmp_path):
    monkeypatch.setenv("QDRANT_URL","https://example.invalid")
    monkeypatch.setenv("QDRANT_API_KEY","test")
    state={"points":[]}
    class Client:
        def __init__(self,**kwargs): pass
        def collection_exists(self,*args): return True
        def get_collection(self,*args):
            return SimpleNamespace(config=SimpleNamespace(params=SimpleNamespace(vectors=models.VectorParams(size=384,distance=models.Distance.COSINE))))
        def create_payload_index(self,*args,**kwargs): pass
        def upsert(self,*args,**kwargs): state["points"].extend(kwargs["points"])
        def count(self,*args,**kwargs): return SimpleNamespace(count=len(state["points"]))
        def close(self): pass
    monkeypatch.setattr(u,"QdrantClient",Client)
    p=tmp_path / "vectors.jsonl"
    point={"id":1,"vector":[0.1]*384,"payload":{"embedding_model":"sentence-transformers/all-MiniLM-L6-v2","source":"a.md","text":"Policy"}}
    p.write_text(json.dumps(point))
    u.upload(p)
    assert len(state["points"]) == 1
    point["vector"]=[0.1]
    p.write_text(json.dumps(point))
    with pytest.raises(ValueError,match="384"):
        u.upload(p)
    assert len(state["points"]) == 1
