# Reference

## Data Schema (Excel)

Each row represents one image:

- `theme`: input theme name
- `element`: representative visual element
- `image_index`: 1-10 within that element
- `search_query`: query used for Pinterest
- `image_url`: collected Pinterest image URL
- `source`: always `pinterest`

## Collection Strategy

For each element, try multiple queries:

1. `{theme} {element} icon 3d flat cute illustration`
2. `{theme} {element} kawaii icon sticker`
3. `{element} flat icon set`

Merge unique URLs in order, stop at 10.

## Robustness Notes

- If Pinterest returns fewer than 10 valid image URLs, export available rows only.
- Prefer URLs containing `pinimg.com`.
- Filter non-http and obvious low-value assets.

## Performance

- Browser: Playwright Chromium
- Concurrency: moderate (default 4)
- Expected duration: depends on network, about several minutes for 50 elements

