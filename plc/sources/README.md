# PLC Sources

Raw scraped content from various sources before atom extraction.

## Subdirectories

- `textbooks/` - University textbooks, online courses (PDF, markdown)
- `vendor_manuals/` - Siemens, Allen-Bradley, Schneider official documentation
- `community/` - Stack Overflow, Reddit, forums, blogs

## Scraping Agents

- **Agent 1:** PLC Textbook Scraper → textbooks/
- **Agent 2:** Vendor Manual Scraper → vendor_manuals/

## File Format

All source files are stored as-is (PDF, HTML, markdown) with metadata JSON:

```json
{
  "source_id": "siemens-s7-1200-manual-2024",
  "source_type": "vendor_manual",
  "source_url": "https://...",
  "scraped_at": "2025-12-09T12:00:00Z",
  "vendor": "siemens",
  "platform": "s7-1200",
  "file_path": "vendor_manuals/siemens/s7-1200-system-manual-2024.pdf"
}
```
