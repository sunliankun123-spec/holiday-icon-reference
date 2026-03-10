# Examples

## Example Request

Input theme:

`Christmas`

Expected behavior:

1. Generate 50 Christmas-related elements.
2. Search Pinterest icon-style images for each element.
3. Export one Excel file with grouped records.

## Example Output Rows

| theme | element | image_index | search_query | image_url | source |
|---|---|---:|---|---|---|
| Christmas | santa claus | 1 | Christmas santa claus icon 3d flat cute illustration | https://i.pinimg.com/... | pinterest |
| Christmas | santa claus | 2 | Christmas santa claus icon 3d flat cute illustration | https://i.pinimg.com/... | pinterest |
| Christmas | reindeer | 1 | Christmas reindeer icon 3d flat cute illustration | https://i.pinimg.com/... | pinterest |

## Example Launch

```bash
pip install -r app/requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload --port 8765
```

PowerShell:

```powershell
./run.ps1
```

