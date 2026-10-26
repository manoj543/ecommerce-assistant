# Standalone revision

- Replaced the integrated assistant with a separate e-commerce-only FastAPI application.
- Removed all general/portfolio routing, profile knowledge dependencies, and old assistant transport/configuration.
- Added a complete independent chat page with responsive layout, policy question suggestions, source chips, clear chat, pending states and server error messages.
- Browser calls this service's POST /api/chat with {"message":"..."}; response is answer/sources/supported.
- Reuses a Groq API key through server environment only, with independently configured generation model.
- Retrieves from Qdrant BEFORE generation; empty retrieval skips Groq.
- Requires JSON generation with supported flag, answer and citations. Invalid/missing/out-of-range citations or abstention return a fixed scope refusal. No general fallback.
- Retained ingestion, vector upload, external-document-folder support, actual vectors and local demo database.
- Added a new-service Render blueprint and deployment guide. No changes to the existing chat assistant repository are needed.
