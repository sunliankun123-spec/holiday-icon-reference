---
name: holiday-icon-reference
description: Collects Pinterest icon references for holidays or themes, generates 50 representative visual elements, and exports an Excel file with 10 unique images per element. Use when the user asks for icon moodboards, holiday visual references, Pinterest icon collection, or Excel image-link aggregation.
---

# Holiday Icon Reference

## Quick Start

When the user asks to collect holiday or theme icon references:

1. Receive the theme name (for example: Christmas).
2. Generate 50 representative visual elements for that theme.
3. Search Pinterest for icon-like images (3D or flat, cute and simplified style).
4. Collect 10 unique image URLs for each element.
5. Export all records to one Excel file.
6. Provide a downloadable output.

## Output Rules

- Source priority: Pinterest.
- Style preference: icon / 3D icon / flat icon / cute / simplified.
- Avoid: realistic photos when possible.
- Quantity target: 50 elements * 10 images each.
- Uniqueness: no duplicate image URL within one element.

## Built-in App

Use the local app in `app/`:

1. Install dependencies:
   - `pip install -r app/requirements.txt`
   - `python -m playwright install chromium`
2. Start service:
   - `uvicorn app.main:app --reload --port 8765`
   - or run `./run.ps1` on Windows PowerShell
3. Open:
   - `http://127.0.0.1:8765`

## Workflow Checklist

- [ ] Confirm the theme text from user input
- [ ] Generate or normalize 50 element keywords
- [ ] Crawl Pinterest image URLs for each element
- [ ] Ensure uniqueness and fill as many as possible toward 10
- [ ] Export `.xlsx` with clear element labels
- [ ] Return download path or download link

## Additional Resources

- Implementation details: [reference.md](reference.md)
- User-facing examples: [examples.md](examples.md)
