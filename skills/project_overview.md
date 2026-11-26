# Project Overview — MS Fragrances

## What we are building
An Agentic AI Customer Experience platform for MS Fragrances (premium attar/perfume shop).
The assistant should be a knowledgeable customer support and product advisor.

## Existing application (DO NOT break)
- FastAPI backend (main.py) with POST /chat.
- AI agent (ai_agent.py) with OpenAI-compatible tool-calling (Cloudflare default, OpenAI fallback).
- Tools: lookup_product (live Google Sheets), recommend_products (deterministic engine).
- Recommendation engine (recommendation_engine.py) with 9-product catalog.
- Product verification against live sheet (verified/price_changed/out_of_stock/not_found/ambiguous/verification_failed).
- Rate limiter (30/min/IP), CORS, MAX_MESSAGE_LENGTH=2000.
- Chat UI (chat_ui.html).
- 16/16 unit tests pass.

## What is missing
- Verified business knowledge (no RAG, no knowledge base).
- Customer question bank.
- Evaluation dataset.
- Business research (YouTube/Instagram not yet collected).

## Guiding principle
Accuracy over answering everything. Never invent business facts, prices, or policies.
Live inventory/prices always come from Google Sheets.
Static business knowledge comes from verified sources only.
