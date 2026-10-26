"""Integration tests: real ONNX embeddings and Qdrant local storage; no Groq key."""
import json
import os
from pathlib import Path
import pytest
from tokenizers import Tokenizer
from fastapi.testclient import TestClient
from app.rag import RagStore, chunk_text, MODEL, source_list

@pytest.fixture(scope="module")
def store(tmp_path_factory):
    os.environ["QDRANT_PATH"] = str(tmp_path_factory.mktemp("qdrant"))
    os.environ.pop("QDRANT_URL", None)
    s = RagStore()
    s.ingest(tmp_path_factory.mktemp("artifacts"))
    yield s
    s.close()

@pytest.mark.parametrize("question,expected", [
    ("How long does standard shipping take?", "01_shipping.md"),
    ("Can I return used shoes after 20 days?", "02_returns.md"),
    ("When will my refund arrive in my bank?", "03_refunds.md"),
    ("Can I cancel after dispatch?", "04_cancellations.md"),
    ("The wrong product arrived. How soon must I report it?", "05_damage_support.md"),
])
def test_retrieval(store, question, expected):
    hits = store.search(question)
    assert hits and hits[0]["source"] == expected

def test_idempotency_and_export(store, tmp_path):
    count = store.client.count(store.collection, exact=True).count
    summary = store.ingest(tmp_path)
    assert store.client.count(store.collection, exact=True).count == count == summary["chunks"]
    chunks = [json.loads(l) for l in (tmp_path / "chunks.jsonl").read_text().splitlines()]
    assert all(0 < c["token_count"] <= 180 for c in chunks)
    vectors = [json.loads(l)["vector"] for l in (tmp_path / "vectors.jsonl").read_text().splitlines()]
    assert all(len(v) == 384 for v in vectors)

def test_no_above_threshold_matches(store):
    assert store.search("Who won yesterday's cricket match?") == []

def test_chunk_coverage():
    tokenizer = Tokenizer.from_pretrained(MODEL)
    tokenizer.no_truncation()
    tokenizer.no_padding()
    text = "Hello, café! Orders are ready. " * 100
    chunks = list(chunk_text(text, tokenizer, size=40, overlap=8))
    assert chunks[0]["start_char"] == 0
    assert chunks[-1]["end_char"] == len(text.rstrip())
    assert all(b["start_char"] <= a["end_char"] for a,b in zip(chunks,chunks[1:]))

def test_citation_filter():
    h = [{"source":"a.md", "id":"a", "score":0.9}]
    assert source_list(h, "Claim [S1]. Fake [S99].")[0]["file"] == "a.md"
    assert source_list(h, "No citation") == []
