"""Upload already generated JSONL points without re-embedding. Cloud only."""
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

def upload(path):
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_API_KEY")
    if not url or not key:
        raise ValueError("Set QDRANT_URL and QDRANT_API_KEY before uploading to Cloud")
    # Validate the complete file before any remote write.
    points = [models.PointStruct.model_validate_json(line)
              for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not points:
        raise ValueError("Vector export is empty")
    for p in points:
        if (not isinstance(p.vector, list) or len(p.vector) != 384
            or not p.payload or p.payload.get("embedding_model") != "sentence-transformers/all-MiniLM-L6-v2"
            or not p.payload.get("text") or not p.payload.get("source")):
            raise ValueError("Expected 384-dimensional MiniLM points with source text metadata")
    collection = os.getenv("QDRANT_COLLECTION", "demoshop_minilm_v1")
    client = QdrantClient(url=url, api_key=key, timeout=30)
    try:
        if not client.collection_exists(collection):
            client.create_collection(collection, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
        config = client.get_collection(collection).config.params.vectors
        if not isinstance(config, models.VectorParams) or config.size != 384 or config.distance != models.Distance.COSINE:
            raise ValueError("Collection schema mismatch; use a new dedicated collection")
        for field in ("embedding_model", "corpus"):
            client.create_payload_index(collection, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD, wait=True)
        for start in range(0, len(points), 64):
            client.upsert(collection, points=points[start:start+64], wait=True)
        print(json.dumps({"uploaded_points":len(points), "collection":collection,
                          "collection_total":client.count(collection, exact=True).count}, indent=2))
    finally:
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(Path(__file__).resolve().parents[1] / "artifacts" / "vectors.jsonl"))
    upload(parser.parse_args().file)
