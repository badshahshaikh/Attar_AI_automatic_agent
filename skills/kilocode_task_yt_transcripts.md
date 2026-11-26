# Kilo Code Task — YouTube Transcript Collection (Phase 3, Task 1)

## Objective
Extract transcripts from business-relevant YouTube videos on channel @SaadAttarwala-f3c and save them as evidence.

## Project
D:\Attar_AI_automatic_agent\

## Videos to process (from inventory)
1. https://www.youtube.com/watch?v=O0Cfk8OLY7Y — "Bakhoor Stock Arrived in India! | Premium Arabic Bakhoor Collection | MS Fragrance" (7:32) — PRIORITY
2. https://www.youtube.com/watch?v=qdEgKj6bYFI — "Al Haramain Attars in India | Original Saudi Attars | Made in KSA" (7:57)
3. https://www.youtube.com/watch?v=zVIkcdmN88g — "My Honest Opinion on Attars | Things Every Attar Lover Should Know" (8:28)

## Steps
1. Open each video page
2. Check if transcript is available (YouTube "Show transcript" button or captions)
3. If available: extract full transcript text with timestamps
4. If not available: note "transcript_unavailable" — do not invent content
5. Save each transcript to: knowledge_base/sources/youtube/transcripts/<video_id>.txt
6. Format: include video URL, title, duration, language, extraction date, then full transcript with timestamps

## Output files
- knowledge_base/sources/youtube/transcripts/O0Cfk8OLY7Y.txt
- knowledge_base/sources/youtube/transcripts/qdEgKj6bYFI.txt
- knowledge_base/sources/youtube/transcripts/zVIkcdmN88g.txt (if accessible)

## Rules
- Never generate fictional transcript content
- If transcript unavailable, create a placeholder noting unavailability
- Keep original transcripts separate from any AI summaries
- Record extraction method and date for each

## Validation
- Each transcript file must exist and contain source URL
- No invented content
