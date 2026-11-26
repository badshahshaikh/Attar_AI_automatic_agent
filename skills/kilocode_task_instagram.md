# Kilo Code Task — Instagram Source Discovery (Phase 3, Task 2)

## Objective
Collect publicly accessible information from Instagram profile @msfragrance_official as evidence.

## Project
D:\Attar_AI_automatic_agent\

## Target URL
https://www.instagram.com/msfragrance_official/

## Steps
1. Navigate to the Instagram profile
2. Collect what is publicly accessible without authentication:
   - Profile bio/description
   - Post URLs visible on the profile
   - Post captions
   - Publication dates (if visible)
   - Product names mentioned
   - Product descriptions
   - Promotional claims
   - Prices mentioned
   - Sizes/variants mentioned
3. If login wall blocks access: document the limitation clearly — do not bypass authentication
4. Save findings to: knowledge_base/sources/instagram/inventory.json

## Output file
- knowledge_base/sources/instagram/inventory.json

## Inventory format
{
  "profile": "https://www.instagram.com/msfragrance_official/",
  "access_status": "accessible" | "restricted" | "login_required",
  "bio": "...",
  "collection_date": "...",
  "posts": [
    {
      "post_url": "...",
      "caption": "...",
      "publication_date": "...",
      "product_names": [...],
      "prices": [...],
      "sizes": [...],
      "claims": [...]
    }
  ],
  "limitations": [...]
}

## Rules
- Use accessible official content only
- Do not bypass authentication, access restrictions, or platform protections
- If content cannot be accessed, document the limitation
- Do not fabricate post content

## Validation
- inventory.json must be valid JSON
- All URLs must be traceable
- No invented post content
