# Architecture — MS Fragrances

## Current architecture
Customer -> Chat UI -> POST /chat (main.py)
  -> rate limiter + CORS
  -> ai_agent.chat()
    -> LLM (Cloudflare/OpenAI) tool-calling
    -> lookup_product (sheets_lookup.py -> Google Sheets live)
    -> recommend_products (recommendation_engine.py + verification via sheets)
  -> reply + tool_calls_made + tool_results + updated_history + observability

## Planned hybrid architecture (future)
- RAG: verified business knowledge (ChromaDB candidate).
- Live APIs: inventory, prices, orders.
- Recommendation engine: product matching.
- LLM: intent, tool selection, conversation, explanation.

## Boundaries
- Business facts -> RAG (verified static knowledge).
- Live prices/stock -> Google Sheets.
- Product recommendations -> deterministic engine.
- LLM must not invent product IDs, prices, availability.
- Agent must verify live data before presenting as current.
