# Help: Running and Updating Universe Stats

## 1) Run locally (Python 3.10+)

```bash
git clone git@github.com:ashish-oraon/universe-stats.git
cd universe-stats
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000

## 2) How universes are loaded

At startup the app reads static JSON files from `data/`:
- `data/H-SUPER45.json`
- `data/H-GOOD45.json`
- `data/H-GOOD200.json`

Each file has the format:

```json
{
  "symbols": ["CHOLAFIN", "HEROMOTOCO", "…"]
}
```

You can manually edit these JSON files to add/remove tickers.

## 3) Regenerate JSON from the reference markdown (optional)

If you maintain the master list in `Hemant_Jain_Stock_Lists_Reference.md`, regenerate JSONs with:

```bash
cd universe-stats
python scripts/generate_universes_json.py
```

This will overwrite the three files in `data/` with symbols parsed from the markdown.

## 4) Troubleshooting

- If the page shows empty tables, ensure files exist in `data/` and contain valid JSON.
- Some tickers may not have Yahoo data; they will show “-” for fields.
- Network must allow HTTPS to Yahoo Finance APIs.

