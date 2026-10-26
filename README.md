# Standalone DemoShop E-commerce RAG

A **separate repository and separate Render FastAPI service** with its own chat page. It has no dependency on your existing general/portfolio assistant, no profile.md, no portfolio routing, and no general-answer mode.

## Architecture

- Browser opens this service's `/` chat page and posts to its own `/api/chat`.
- FastAPI embeds the question using MiniLM (384 dimensions).
- Qdrant searches the dedicated policy collection and returns matching passage text.
- Groq receives the question and retrieved passages. It generates a source-cited policy answer or abstains.
- If there is no evidence, invalid JSON, missing citations, invalid citation IDs, or a model-declared unsupported question, the backend returns a fixed refusal. It never switches to general chat.

Groq does not connect to Qdrant itself: FastAPI performs retrieval and supplies the evidence. No training/fine-tuning is required. You may reuse the same Groq API key in the NEW service's server environment. That reuses the provider account/key, not the old chat service. Model ID is configured independently by GROQ_MODEL. Both services consume that account's applicable limits.

## Files

| Path | Purpose |
|---|---|
| app/main.py | Standalone FastAPI lifecycle, page, RAG chat and grounded-output validation |
| app/static/ | Included chat page, CSS and browser JavaScript |
| app/rag.py | MiniLM embeddings, tokenization, Qdrant ingestion and vector search |
| app/ingest.py | Generate fresh embeddings and synchronize documents |
| app/upload_vectors.py | Upload the supplied vectors to Qdrant Cloud |
| app/search.py | Inspect vector search independently of Groq |
| documents/ | Five fictional policy documents |
| artifacts/ | Real tokenization, vectors, ingestion summary and search examples |
| qdrant_data/ | Included local-mode demo index; NOT for hosted persistence |
| render.yaml | Blueprint for a NEW free Render service |
| DEPLOY_RENDER.md | Detailed new-service deployment instructions |

## 1. Local setup

Use Python 3.11 or 3.12, from this extracted repository directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux/macOS: use `source .venv/bin/activate` and `cp .env.example .env` instead.

Set these in .env:

```dotenv
GROQ_API_KEY=YOUR-EXISTING-GROQ-KEY
GROQ_MODEL=AN-ACTIVE-GROQ-CHAT-MODEL-SUPPORTING-JSON-OUTPUT
QDRANT_URL=https://YOUR-CLUSTER-ENDPOINT
QDRANT_API_KEY=YOUR-QDRANT-DATABASE-KEY
QDRANT_COLLECTION=demoshop_minilm_v1
```

Choose a model supporting `response_format: {"type":"json_object"}`; see https://console.groq.com/docs/structured-outputs. Never put API keys in app/static files. All browser requests go only to this FastAPI server.

## 2. Upload policy vectors

If you have already uploaded the same sample corpus to the SAME collection, you can reuse it; re-upload is not necessary. To isolate this app completely, choose a new QDRANT_COLLECTION and upload the supplied points:

```bash
python -m app.upload_vectors
python -m app.search "How soon must I report a damaged item?"
```

The upload command reads the existing actual 384-dimensional vectors in artifacts/vectors.jsonl, creates a cosine collection and required payload indexes, and upserts 10 points. It does not call Groq or download an embedding model. Search downloads the public ONNX encoder on first use.

To regenerate embeddings after editing the policies:

```bash
python -m app.ingest
```

Sources need not live in Git. You can instead run:

```bash
python -m app.ingest --documents "C:/my-documents/demoshop"
```

The loader reads Markdown files in that folder. Qdrant stores chunk text with the vectors, so the chat server does not read source documents at runtime. Keep source backups for future rebuilds. Ingestion treats the selected folder as the entire sample corpus and removes its obsolete chunks; do not supply only a partial update folder. The vector upload command upserts only and does not prune old points. Perform updates separately from serving traffic in this small demo.

## 3. Run the independent chat service

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 1
```

Open http://127.0.0.1:8001/ for the NEW chat page, or /docs for the API. Port 8001 allows your other local assistant to keep using port 8000.

```json
{"message":"Can I return shoes after wearing them for 20 days?"}
```

Response: `answer`, `sources` (citation/file/chunk/score) and `supported`. Supported answers include inline [S1] labels matching the source chips. Exact wording is model-dependent.

The interface displays a transcript, but each submitted question is independent. Ask complete questions, e.g. "How long does a prepaid refund take?" rather than "How long?". This keeps unrelated prior answers out of retrieval and generation. No chat persistence or conversational query rewriting is implemented.

## 4. Deploy separately

Follow **DEPLOY_RENDER.md**. Put THIS directory's contents at the root of a NEW GitHub repository. Create a NEW Render Web Service connected to it. Do not merge anything into the old assistant repository. This service hosts both its page and API, so no separate frontend deployment or CORS configuration is needed.

Keep the same Groq key if desired, and use your own selected model ID. Changing the Groq generation model does not require re-embedding; changing the MiniLM embedding model does.

## Behavior and practical limits

This is a fictional e-commerce policy assistant. It cannot access live orders, confirm payment status, cancel orders, or submit returns. The provided sample policies are not real business terms.

Only evidence-based e-commerce answers are requested from Groq. No retrieval matches skips generation entirely. Other cases are checked using structured output and citation validation. This reduces unsupported answers but cannot mathematically guarantee grounding or prevent every prompt injection; evaluate your selected live model on unrelated questions and misleading instructions. Citation IDs prove passage selection, not semantic correctness of every claim.

MIN_SCORE=0.35 and TOP_K=4 are starting values, not calibrated confidence. Evaluate relevant/irrelevant questions before tuning. The first RAG request downloads/loads the CPU embedding model, adding cold-start latency and memory use. Confirm the instance has enough memory. One lazy shared encoder/client is reused and closed on shutdown.

Use one worker. The global per-minute cap and concurrency semaphore protect this small public demo and are not distributed multi-instance limits. There is no public ingestion endpoint. No API secrets are sent to the browser; browser text is rendered with textContent rather than injected HTML.

For local Qdrant only: leave QDRANT_URL blank, run ingestion while the server is stopped, then start the server. Local database files use an exclusive lock. On Render, QDRANT_URL is required to avoid relying on ephemeral disk.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Real embedding/retrieval tests need the model download on first use. Groq and cloud-upload API tests use mocks and require no live key. See VALIDATION.md for the exact checks performed for this revision.
