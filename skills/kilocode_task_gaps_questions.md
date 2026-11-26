# Kilo Code Task — Information Gaps & Question Bank (Phase 3, Tasks 5-6)

## Objective
Update information gaps and expand the customer question bank based on collected evidence.

## Project
D:\Attar_AI_automatic_agent\

## Input
- knowledge_base/evidence/evidence_registry.json
- knowledge_base/evaluation/information_gaps.md (existing)
- knowledge_base/evaluation/customer_questions.json (existing, 15 questions)

## Output files
- knowledge_base/evaluation/information_gaps.md (updated)
- knowledge_base/evaluation/customer_questions.json (expanded)

## Task 5 — Information gap analysis
Identify information that cannot be established from collected sources.
Examples to check:
- Return policy
- Refund policy
- Delivery timelines
- Wholesale minimum order quantity
- Payment methods
- Business history
- Product authenticity claims
- Customer support timings
- Contact details (phone, email, address)

Update information_gaps.md with questions requiring business owner confirmation.

## Task 6 — Customer question bank expansion
Expand customer_questions.json beyond the existing 15 questions.
For each new question:
{
  "question_id": "FAQ-0016",
  "category": "...",
  "question": "...",
  "intent": "...",
  "expected_answer": null,
  "required_sources": [...],
  "answer_type": "ANSWERABLE|LIVE_DATA_REQUIRED|INFORMATION_MISSING|hybrid",
  "verification_status": "pending",
  "requires_business_confirmation": true/false
}

Categories to cover:
- Business identity
- Product discovery
- Fragrance recommendations
- Product comparisons
- Attar education
- Product usage
- Pricing
- Availability
- Ordering
- Payments
- Shipping
- Wholesale
- Returns
- Customer support

Rules:
- Do not invent expected answers
- Mark unverified as INFORMATION_MISSING or LIVE_DATA_REQUIRED
- Use actual findings where possible

## Validation
- customer_questions.json must be valid JSON
- All question_ids unique (FAQ-XXXX format)
- No invented answers
- information_gaps.md updated with missing items
