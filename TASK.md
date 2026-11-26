# TASK.md — Next Step for Kilo Code

Source: ChatGPT (new conversation "Build Next Feature", generated after project context was provided).

## Goal

Build a **Product Discovery & Recommendation Engine** on top of the existing MS Fragrances AI Product Assistant. Turn the app from a pure inventory-lookup chatbot into a product sales assistant that can suggest products based on customer preferences, budget, scent, occasion, etc.

Do NOT replace the existing inventory tool (`lookup_product` / `sheets_lookup.py`). Add a new `recommend_products` tool to the existing agent loop.

## Target architecture

Understand customer intent → filter products → rank recommendations → verify live inventory → respond naturally.

The AI decides when to use the recommendation tool. Python code performs filtering and ranking **deterministically** — never let the LLM invent recommendations.

Flow: User → Agent (OpenAI) → `recommend_products` tool → recommendation engine (Python) → product catalog + live sheet verification → Agent composes final reply.

Keep the ranking simple for MVP. Avoid embeddings, vector databases, and extra LLM calls at this stage.

## Step 1 — Add structured product attributes (Phase 1)

Add verified fragrance attributes to the product catalog (Google Sheet and/or a local catalog). Start with the top 15–20 most popular products. Do not enrich the whole catalog at once.

New columns/fields to add:

| Field | Example |
|---|---|
| product_name | Oud Marj |
| scent_family | Woody, Oud |
| scent_notes | Woody, smoky, warm |
| intensity | Strong (light / moderate / strong) |
| longevity | Long lasting |
| occasion | Evening, special occasion |
| season | Winter, all season |
| target_audience | Unisex |
| price_min | 299 |
| available_sizes | 3ml, 6ml, 12ml |
| description | Rich woody oud profile |
| tags | oud, woody, bold, evening |

Rules:
- Never let the AI guess fragrance characteristics, longevity, intensity, or scent notes.
- Populate from verified product info, or mark unknown.
- Live price/stock still come from the Google Sheet via `lookup_product`.

## Step 2 — Create `recommendation_engine.py` (Phase 2)

New file at project root: `D:\Attar_AI_automatic_agent\recommendation_engine.py`. Must be independent of FastAPI and the OpenAI agent.

Responsibilities:
- Load product catalog.
- Filter by budget, preferences, availability.
- Rank matching products.
- Return best 3–5 candidates.
- Never invent prices or attributes.

Suggested function:

```python
def recommend_products(
    budget: float | None = None,
    scent_family: list[str] | None = None,
    intensity: str | None = None,
    occasion: list[str] | None = None,
    preferred_notes: list[str] | None = None,
    limit: int = 3
) -> list[dict]:
    ...
```

Filtering logic:
1. Hard constraints first: budget, requested product type, requested size (when specified), available stock.
2. Then rank remaining candidates by soft preferences:

| Match | Score |
|---|---|
| Exact scent-family match | +5 |
| Matching scent note | +3 |
| Matching occasion | +3 |
| Matching intensity | +2 |
| Matching season | +1 |

Return predictable results for the same catalog + inputs.

## Step 3 — Add `recommend_products` tool to `ai_agent.py` (Phase 3)

Register a new tool in the existing OpenAI tool-calling loop alongside `LOOKUP_TOOL_SCHEMA`. Tool schema:

```python
RECOMMEND_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recommend_products",
        "description": (
            "Recommend MS Fragrances products based on customer preferences, "
            "budget, scent profile, occasion, intensity, and product type. "
            "Use when the customer wants suggestions or help choosing a product."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "budget": {"type": "number", "description": "Maximum budget in INR"},
                "scent_family": {"type": "array", "items": {"type": "string"}},
                "intensity": {"type": "string", "enum": ["light", "moderate", "strong"]},
                "occasion": {"type": "array", "items": {"type": "string"}},
                "preferred_notes": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer", "default": 3},
            },
        },
    },
}
```

Pass both tools to `chat.completions.create(tools=[LOOKUP_TOOL_SCHEMA, RECOMMEND_TOOL_SCHEMA], ...)`.

When the agent calls `recommend_products`:
1. Parse arguments.
2. Run `recommendation_engine.recommend_products(...)`.
3. Retrieve matching products.
4. Verify price and availability using the existing Sheets lookup (`lookup_product`) where needed.
5. Return structured JSON to the agent.
6. Let the LLM compose the final response in the customer's language.

Do not return only product names — return structured info so the agent can explain why each was recommended.

## Step 4 — Update `prompts/system_prompt.txt` (Phase 4)

Append (do not rewrite) a new section:

```
Product Discovery and Recommendation Rules

You are a helpful fragrance advisor for MS Fragrances.

When customers ask for product suggestions, recommendations, help choosing an attar, or describe a scent they want:

Use the recommend_products tool to find suitable products.

Understand the customer's budget, preferred scent, occasion, intensity, and other preferences.

Never invent fragrance notes, longevity, intensity, or product properties.

Recommend a maximum of 3 products at a time.

Explain briefly why each product matches the customer's preferences.

Respect the customer's budget. Do not recommend products above their stated budget.

Verify current prices and stock using the inventory lookup tool when necessary.

If the customer's preferences are unclear, ask one natural follow-up question rather than asking multiple questions together.

If no exact match is available, suggest the closest alternatives and clearly explain the difference.

Use natural conversational language. Respond in English, Hindi, or Hinglish based on the customer's language.

Do not overwhelm customers with product lists. Help them choose.
```

Keep existing inventory lookup rules intact.

## Step 5 — Define recommendation response format (Phase 5)

Tool should return consistent JSON:

```json
{
  "status": "success",
  "products": [
    {
      "product_name": "Oud Marj",
      "matched_attributes": ["woody", "strong", "evening"],
      "price": 399,
      "size": "6ml",
      "in_stock": true,
      "reason": "Matches your preference for strong woody fragrances."
    }
  ]
}
```

Tool provides the facts; LLM provides the conversational explanation. Example customer-facing reply:

> If you like strong, woody fragrances for evenings, I'd suggest these:
> 1. Oud Marj — ₹399
>    A good option if you enjoy warm, woody fragrances with a noticeable presence.
> 2. Black Oud — ₹499
>    A bolder oud-style option if you prefer something deeper.
> Are you looking for something for daily use or special occasions?

Only use example descriptions/prices in real responses if verified against the catalog.

## Step 6 — Build test set (Phase 6)

Create `tests/test_recommendations.py` and test the engine independently of OpenAI.

| Test input | Expected behavior |
|---|---|
| Budget ₹300 | No product above ₹300 |
| Budget ₹500, strong scent | Rank strong products under ₹500 |
| Woody fragrance | Rank woody products first |
| Product unavailable | Do not recommend as available |
| No matching attributes | Return sensible alternatives or no results |
| No budget | Rank by preference, not price assumptions |
| Exact size requested | Only recommend compatible sizes |
| Empty catalog | Return empty result safely |

Engine must return predictable results for same catalog + inputs.

## Step 7 — Suggested project structure

```
app/ (or keep current flat structure)
├── main.py
├── ai_agent.py
├── sheets_lookup.py
├── recommendation_engine.py    # NEW
├── catalog_service.py          # NEW (optional)
├── prompts/
│   └── system_prompt.txt
├── tests/
│   └── test_recommendations.py
└── chat_ui.html
```

If the existing project doesn't use an `app/` package, keep the current flat structure (files at `D:\Attar_AI_automatic_agent\`) instead of refactoring just to match this layout.

## Implementation order (do not break existing assistant)

1. Phase 1 — Product catalog enrichment (attributes for top 15–20 products).
2. Phase 2 — Recommendation engine (`recommendation_engine.py` + independent tests).
3. Phase 3 — Agent integration (register tool in OpenAI loop, handle results).
4. Phase 4 — Prompt update (append recommendation rules).
5. Phase 5 — Testing (budgets, preferences, unavailable products, Hinglish queries, multi-turn conversations).

## What NOT to build yet

Deliberately postpone:
- Vector database / RAG for recommendations
- Multi-agent architecture
- Agent memory database
- Fine-tuning
- WhatsApp API integration
- Complex recommendation analytics
- A second LLM for ranking products

The current tool-calling architecture is sufficient.

## Definition of done

Feature is complete when a customer can say:

> "Mujhe ₹500 ke andar koi achha strong attar suggest karo jo daily use kar saku."

And the assistant can:
- Understand the Hinglish request.
- Extract budget and scent preference.
- Recommend relevant products from the actual catalog.
- Verify stock and prices.
- Explain its recommendations.
- Ask one natural follow-up question if preferences are unclear.
