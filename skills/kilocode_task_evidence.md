# Kilo Code Task — Evidence Registry Population (Phase 3, Task 3)

## Objective
Populate evidence_registry.json with traceable evidence items from collected YouTube transcripts and Instagram content.

## Project
D:\Attar_AI_automatic_agent\

## Input files
- knowledge_base/sources/youtube/transcripts/*.txt
- knowledge_base/sources/instagram/inventory.json
- knowledge_base/evidence/source_registry.json

## Output file
- knowledge_base/evidence/evidence_registry.json

## Evidence schema
Each entry:
{
  "evidence_id": "EV-0001",
  "claim": "specific statement from source",
  "source_id": "SRC-0001",
  "original_url": "https://...",
  "timestamp": "00:04:32",
  "evidence_excerpt": "original transcript/caption excerpt",
  "category": "business_information|product|pricing|operations|education",
  "verification_status": "UNVERIFIED",
  "confidence": null,
  "review_status": "pending"
}

## Steps
1. Read each transcript file
2. Identify business-related claims (products, pricing, sizes, operations, brand info)
3. For each claim, create an evidence entry with source reference
4. Read Instagram inventory and create evidence entries for product/price/size claims
5. Use source_id from source_registry.json (SRC-0001 = YouTube, SRC-0002 = Instagram)
6. Set verification_status to "UNVERIFIED" (not yet confirmed)
7. Set confidence to null
8. Set review_status to "pending"

## Rules
- Every evidence item must reference an existing source_id
- Every claim must have supporting original material (excerpt)
- No invented claims
- AI-generated summaries must NOT become primary evidence
- Evidence IDs must be unique (EV-0001, EV-0002, ...)

## Validation
- evidence_registry.json must be valid JSON
- All evidence_ids unique
- All source_ids reference existing sources
- No empty claims or excerpts
