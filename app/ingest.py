"""Run on your laptop, separately from the chat server."""
import argparse
import json
from app.rag import RagStore

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--documents", help="Folder with Markdown files; defaults to documents/ or DOCUMENTS_DIR")
    args = parser.parse_args()
    store = RagStore()
    try:
        print(json.dumps(store.ingest(documents=args.documents), indent=2))
    finally:
        store.close()
