# Hemant Jain Universe Dashboard

FastAPI web app that parses `Hemant_Jain_Stock_Lists_Reference.md` and shows live market stats for H-SUPER45, H-GOOD45, and H-GOOD200 universes. Data is fetched on-demand from Yahoo Finance.

## Features
- Parses universe lists directly from the markdown file, no manual sync needed
- Computes Price, SMA50, SMA200, % > 200DMA, 52W Low/High, distances
- Clean, responsive tables per universe

## Requirements
- Python 3.10+

## Quick Start

```bash
cd /home/oraon-as/Documents/Personal/Trading
python3 -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements.txt
uvicorn webapp.main:app --reload --host 0.0.0.0 --port 8000
```

Then open: http://localhost:8000

## Notes
- Data loads on each page open; first load may take time depending on list sizes.
- Tickers are treated as NSE symbols; `.NS` is appended for Yahoo Finance unless a suffix already exists.


