# Kilo Code Task — Business Information Extraction (Phase 3, Task 4)

## Objective
Extract MS Fragrances business information from collected evidence and save to knowledge base documents.

## Project
D:\Attar_AI_automatic_agent\

## Input
- knowledge_base/evidence/evidence_registry.json
- knowledge_base/sources/youtube/transcripts/*.txt
- knowledge_base/sources/instagram/inventory.json

## Output files
- knowledge_base/business/company_profile.md
- knowledge_base/business/brand_information.md
- knowledge_base/business/business_operations.md
- knowledge_base/business/contact_information.md
- knowledge_base/products/product_knowledge.md
- knowledge_base/products/product_categories.md

## Steps
1. Review all evidence items
2. Group claims by category: business identity, brand, products, operations, contact
3. Write each document with only evidence-backed information
4. For each claim, include source reference (URL + timestamp)
5. Mark unverified claims clearly
6. Do not invent business policies (returns, shipping, payments) — mark as missing

## Document format
Each .md file:
# Section Title
Status: VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED

## Claim
Text of claim with [source: URL, timestamp]

## Information gaps
- List what is not known

## Rules
- Only include claims with supporting evidence
- Distinguish verified facts from unverified claims
- Never present unverified policies as confirmed
- External brand info (Ajmal, Surrati) = general education only, never attributed to MS Fragrances

## Validation
- All .md files must exist
- Every claim must have source reference
- No invented business information
