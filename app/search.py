import argparse
import json
from app.rag import RagStore

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    args = parser.parse_args()
    store = RagStore()
    try:
        print(json.dumps(store.search(args.question), indent=2))
    finally:
        store.close()
