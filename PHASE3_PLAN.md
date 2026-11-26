# Phase 3 — Business Intelligence Collection & Evidence Verification

**Project:** D:\Attar_AI_automatic_agent\
**Goal:** Collect authentic, source-backed MS Fragrances business info before RAG.
**Timeline:** Complete today (few hours).
**Rule:** No RAG, no ChromaDB, no agent code changes, no system prompt changes.

## Source identity (verified)
- YouTube @SaadAttarwala-f3c = Saad's personal channel; Saad owns MS Fragrances → candidate source
- Instagram @msfragrance_official → candidate source
- msfragrance.in → official website (confirmed by user)
- YouTube About page: NO Instagram link, NO website link found (source identity unverified)

## Tasks for Kilo Code (small, sequential)

### Task A — YouTube source inventory (DONE, verify)
- 6 videos discovered on @SaadAttarwala-f3c
- File: knowledge_base/sources/youtube/inventory.json
- 3 videos with titles captured, 3 partial (timestamps only)

### Task B — YouTube transcript collection
- Extract transcripts from business-relevant videos
- Prioritize: "Bakhoor Stock Arrived... MS Fragrance" (O0Cfk8OLY7Y)
- Save transcripts to knowledge_base/sources/youtube/transcripts/
- Record video URL, timestamp, language, extraction method, date

### Task C — Instagram source discovery
- Navigate to https://www.instagram.com/msfragrance_official/
- Collect: post URLs, captions, publication dates, product names, prices, sizes
- Save to knowledge_base/sources/instagram/inventory.json
- Document access restrictions if any

### Task D — Evidence registry population
- Add evidence items to knowledge_base/evidence/evidence_registry.json
- Each evidence: evidence_id, claim, source_id, original_url, timestamp, evidence_excerpt, category, verification_status, confidence, review_status
- Use source IDs from source_registry.json

### Task E — Business information extraction
- Extract business identity, products, pricing, operations from transcripts/captions
- Save to knowledge_base/business/company_profile.md, product_knowledge.md, etc.
- Every claim must reference source URL + timestamp

### Task F — Information gap analysis
- Update knowledge_base/evaluation/information_gaps.md
- List: return policy, refund policy, delivery timelines, MOQ, payment methods, business history, contact info

### Task G — Customer question bank expansion
- Expand knowledge_base/evaluation/customer_questions.json beyond 15 questions
- Use actual findings; mark unverified as INFORMATION_MISSING or LIVE_DATA_REQUIRED
- Do not invent answers

### Task H — Quality control & validation
- Validate all JSON against schemas in knowledge_base/schemas/
- Run existing tests: 16/16 must remain passing
- Report: videos discovered, transcripts collected, evidence items, gaps, question count

## Deliverables (final report)
1. Complete YouTube source inventory
2. Instagram research inventory
3. Transcripts or references
4. Structured evidence registry
5. Updated source registry
6. Extracted business information
7. External educational research
8. Updated customer question bank
9. Information gap report
10. Research methodology report
