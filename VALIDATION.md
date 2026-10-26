# Standalone revision validation — 26 October 2026

## Executed

- Full test suite: **24 passed**, with one upstream Starlette/httpx TestClient deprecation warning.
- Real MiniLM embeddings and local Qdrant ingestion/retrieval: five policy queries ranked the expected document first; an unrelated cricket query had no matches.
- Actual included corpus: five fictional documents, 10 chunks, 384 dimensions, 1,114 chunk tokens including overlap. Tokenization IDs, vector exports and the prior local demo index are bundled.
- Verified idempotent ingestion, vector dimensions, chunk coverage and source metadata.
- Standalone chat page and CSS/JavaScript routes served successfully through FastAPI TestClient.
- API tests verified supported citation-bearing responses, no-match abstention without calling Groq, unrelated-question abstention, invalid JSON/unsupported outputs, citation mismatches, out-of-range citation rejection, blank/overlength questions, missing configuration and request caps.
- Verified no general or portfolio API route exists and that question/evidence messages are passed to the Groq client with zero temperature and JSON response format.
- Existing Cloud upload contract tests verified credential requirements and vector validation/upsert using a mocked Qdrant client.
- Python compilation and JavaScript syntax check passed.

## Not executed

- Live Groq generation, Qdrant Cloud upload, and Render deployment: no credentials/access supplied. Provider and cloud write tests use mocks, not actual external accounts.
- Browser visual inspection: the browser binary download failed in this environment. Page/asset serving and JavaScript syntax were checked; interactive browser layout and behavior still need a browser check.

Scope enforcement uses retrieval thresholds, explicit model instructions, an abstention flag and citation validation. This is not a formal proof that every generated statement is entailed by the sources. Evaluate live outputs with your chosen model before relying on them.

The model cache is not included. A new host downloads MiniLM on first use, requiring internet, memory and cold-start time. The frontend contains no API key. Source documents and local vector artifacts are reproducibility assets; Cloud text payloads supply runtime context.
