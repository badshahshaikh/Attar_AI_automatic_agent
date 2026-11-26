# Knowledge Base Standards — MS Fragrances

## Verification statuses
- VERIFIED: directly supported by authoritative source.
- PARTIALLY_VERIFIED: some support, needs more verification.
- UNVERIFIED: no reliable evidence.
- CONFLICTING: sources disagree.
- OUTDATED: may no longer be current.

## Answer types (customer question bank)
- ANSWERABLE: verified knowledge sufficient.
- LIVE_DATA_REQUIRED: needs current inventory/price/order data.
- INFORMATION_MISSING: insufficient business info.

## Evidence schema (evidence_registry.json entries)
evidence_id, claim, source_id, original_url, timestamp, evidence_excerpt,
category, verification_status, confidence, review_status.

## Source schema (source_registry.json entries)
source_id, platform, source_name, source_url, content_type, author_channel,
publication_date, collection_date, access_status, review_status.

## Question schema (customer_questions.json entries)
question_id, category, question, intent, expected_answer, required_sources,
answer_type, verification_status, requires_business_confirmation.

## Rules
- All business docs must be traceable to evidence.
- Keep frequently changing inventory/prices outside static KB (Google Sheets is source of truth).
- Never present unverified policies as confirmed.
- Use JSON with unique IDs; validate before use.
