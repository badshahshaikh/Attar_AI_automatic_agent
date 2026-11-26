# Next Steps — MS Fragrances (Current: Phase 3)

## Immediate — Phase 3: Business Intelligence Collection

### Task 1 — YouTube transcript collection (NEXT)
Collect transcripts from business-relevant YouTube videos on @SaadAttarwala-f3c.
- Priority video: "Bakhoor Stock Arrived... MS Fragrance" (https://www.youtube.com/watch?v=O0Cfk8OLY7Y)
- Save transcripts to knowledge_base/sources/youtube/transcripts/
- Record: video URL, timestamp, language, extraction method, extraction date
- Do NOT invent transcript content

### Task 2 — Instagram source discovery
Navigate https://www.instagram.com/msfragrance_official/
- Collect: post URLs, captions, dates, product names, prices, sizes, claims
- Save to knowledge_base/sources/instagram/inventory.json
- Document access restrictions if any

### Task 3 — Evidence registry population
Add evidence items to knowledge_base/evidence/evidence_registry.json
- Schema: evidence_id, claim, source_id, original_url, timestamp, evidence_excerpt, category, verification_status, confidence, review_status

### Task 4 — Business information extraction
Extract business identity, products, pricing, operations from transcripts/captions
- Save to knowledge_base/business/*.md and products/*.md
- Every claim must reference source URL + timestamp

### Task 5 — Information gap analysis
Update knowledge_base/evaluation/information_gaps.md
- List unverified: return policy, refund, delivery, MOQ, payments, business history, contact

### Task 6 — Customer question bank expansion
Expand knowledge_base/evaluation/customer_questions.json beyond 15 questions
- Mark unverified as INFORMATION_MISSING or LIVE_DATA_REQUIRED
- Do not invent answers

### Task 7 — Quality control & validation
- Validate JSON against schemas in knowledge_base/schemas/
- Run tests: 16/16 must pass
- Prepare final report

## Rules
- No RAG, no ChromaDB, no agent code changes, no system prompt changes
- Preserve existing Git changes (system_prompt.txt, __pycache__)
- Do not commit without user approval
- Every factual claim needs traceable source
