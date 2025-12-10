# PLC Chunks

Chunked content from sources, ready for atom extraction.

## Purpose

After scraping, source files are chunked into smaller segments:
- **PDF pages** → 1-2 page chunks
- **Textbook chapters** → section-level chunks
- **Web pages** → topic-level chunks

## Processing Pipeline

```
sources/ → chunking → chunks/ → atom extraction → atoms/
```

## File Format

Each chunk is a JSON file:

```json
{
  "chunk_id": "chunk-abc123",
  "source_id": "siemens-s7-1200-manual-2024",
  "chunk_index": 42,
  "content": "Chapter 5: Timer Instructions...",
  "metadata": {
    "page_number": 42,
    "section": "Timer Instructions",
    "vendor": "siemens",
    "platform": "s7-1200"
  },
  "chunked_at": "2025-12-09T12:05:00Z"
}
```

## Chunking Strategy

- **Max chunk size:** 2,000 tokens (for embedding generation)
- **Overlap:** 200 tokens (preserve context across chunks)
- **Boundary:** Respect section/paragraph boundaries
