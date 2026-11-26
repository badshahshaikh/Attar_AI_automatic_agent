# MS Fragrances — Initial Project Investigation Report

**Project path:** `D:\Attar_AI_automatic_agent\`
**Investigation type:** Read-only (no source files modified)
**Date:** 2026-11-24

## 1. Complete project structure

```
Attar_AI_automatic_agent/
├── .env / .env.example
├── .gitignore
├── README.md
├── TASK.md
├── ai_agent.py
├── chat_ui.html
├── create_sample_excel.py
├── main.py
├── product_lookup.py
├── recommendation_engine.py
├── requirements.txt
├── sheets_lookup.py
├── data/
│   └── products.xlsx
├── prompts/
│   └── system_prompt.txt
└── tests/
    └── test_recommendations.py
```

## 2. Technologies

- Backend: FastAPI (Python 3.10), Pydantic v2
- Server: Uvicorn
- LLM provider: OpenAI-compatible (default Cloudflare Workers AI; OpenAI fallback)
- Inventory: Google Sheets (live, no cache)
- Legacy inventory: Excel (pandas) — superseded by sheets_lookup
- Frontend: single HTML file (chat_ui.html, ~1090 lines)
- Tests: custom unittest-style script (16 tests)

## 3. Architecture & data flow

Customer → Chat UI (chat_ui.html) → POST /chat (main.py)
  → rate limiter + CORS middleware
  → ai_agent.chat()
    → loads system prompt
    → LLM (Cloudflare/OpenAI) with tool-calling
    → tools:
        - lookup_product (sheets_lookup.py → Google Sheets live)
        - recommend_products (recommendation_engine.py catalog + verification via sheets)
    → returns reply + tool_calls_made + tool_results + updated_history + observability

## 4. File responsibilities

- main.py: FastAPI app, /chat endpoint, Pydantic models (VerificationStatus, RecommendationProduct, etc.), CORS, per-IP rate limiter (30/min), MAX_MESSAGE_LENGTH (2000).
- ai_agent.py: LLM client (Cloudflare default), agentic loop (MAX_ITERATIONS=10), system prompt loader, tool schemas, recommendation verification logic, observability.
- sheets_lookup.py: live Google Sheets fetch, fuzzy name/alias match, size filter.
- product_lookup.py: legacy Excel lookup (not wired into main flow).
- recommendation_engine.py: in-memory catalog (9 products), deterministic filtering/scoring, MAX_RECOMMENDATIONS=3.
- prompts/system_prompt.txt: agent rules + recommendation rules.
- chat_ui.html: WhatsApp-style UI.
- tests/test_recommendations.py: 16 unit tests (all passing).

## 5. Existing functionality

- Live inventory lookup from Google Sheets (no caching).
- Product recommendation engine with deterministic scoring.
- Recommendation verification against live sheet (verified/price_changed/out_of_stock/not_found/ambiguous_match/verification_failed).
- Rate limiting, CORS, request size limits.
- Observability (duration, tool usage, errors).
- Conversation history with follow-ups.
- Hinglish/English support via system prompt.

## 6. Agent execution flow

1. Empty/non-string message → graceful rejection.
2. History capped to MAX_HISTORY_TURNS (20).
3. System prompt loaded fresh each request.
4. Agentic loop up to 10 iterations; tools auto-selected.
5. Duplicate tool call detection → force answer.
6. After 2 tool rounds → force answer (tool_choice=none).
7. On exception → safe generic reply.

## 7. External integrations

- Google Sheets API (service account) — live inventory.
- LLM provider (Cloudflare Workers AI default, OpenAI fallback).
- (Planned) YouTube/Instagram business research — not yet implemented.

## 8. Existing limitations / technical debt

- No RAG / vector DB / business knowledge base yet.
- No tests for API endpoints, sheets, or agent integration (only engine unit tests).
- Legacy product_lookup.py (Excel) still present but unused.
- Catalog is small (9 products) and hardcoded in recommendation_engine.py.
- No authentication/authorization; CORS origins configurable.
- In-memory rate limiter (not distributed).
- No structured logging of customer PII review beyond guidance.
- No evaluation dataset for LLM responses.
- .gitignore ignores *.json (may hide legitimate json configs).

## 9. Reusable vs rebuild

Reusable: FastAPI skeleton, agent loop, sheets lookup, recommendation engine, verification logic, UI.
Rebuild/add: business knowledge (RAG), customer question bank, evaluation harness, source registry.

## 10. Security observations

- Secrets via .env; .env gitignored.
- No secrets in source.
- CORS restricted to localhost by default.
- Rate limiting present.
- Pydantic validation on request/response.
- Tool args validated in agent.

## 11. Git state

- Branch: main
- Last commit: 9505b2e "Add unit tests for the recommendation engine"
- Uncommitted: prompts/system_prompt.txt (recommendation rules appended), __pycache__ (noise), TASK.md (untracked).

## 12. Test results

- tests/test_recommendations.py: 16/16 passed.
- py_compile: all source files compile.

## 13. Missing business information

- No verified MS Fragrances business facts collected yet.
- YouTube channel (@SaadAttarwala-f3c) and Instagram (@msfragrance_official) provided but not yet researched.
- Customer question bank not yet created.
- No knowledge base documents.

## 14. Recommended next phases (per ChatGPT)

1. Business research (YouTube/Instagram) — collect verified facts with sources.
2. Customer question bank.
3. Knowledge base documents.
4. RAG architecture (ChromaDB evaluation).
5. Agentic integration (RAG as a tool).
6. Evaluation & testing.
7. Production readiness.

## 15. Files that should NOT be changed during investigation

None modified. Investigation was read-only.
