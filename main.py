from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from parsers.json_loader import load_universes_from_json, load_universes_with_prefixes
from services.market_data import fetch_stats_for_symbols


APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT / "data"

app = FastAPI(title="Hemant Jain Universe Dashboard")

static_dir = APP_ROOT / "static"
templates_dir = APP_ROOT / "templates"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Cache universes parsed from MD at startup; the data itself is fetched fresh per request
UNIVERSE_SYMBOLS: Dict[str, List[str]] = {}


@app.on_event("startup")
def startup_event() -> None:
    global UNIVERSE_SYMBOLS
    UNIVERSE_SYMBOLS = load_universes_from_json(DATA_DIR)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "landing.html",
        {"request": request},
    )


@app.get("/india", response_class=HTMLResponse)
def india(request: Request) -> HTMLResponse:
    # Fetch latest stats for each universe on each request
    universe_data: Dict[str, List[dict]] = {}
    for universe_name, symbols in UNIVERSE_SYMBOLS.items():
        stats = fetch_stats_for_symbols(symbols, max_workers=8, default_suffix="NS")
        rows = [s.as_dict() for s in stats]
        universe_data[universe_name] = rows
    # Sort universe sections in the desired order
    ordered_universes = ["H-SUPER45", "H-GOOD45", "H-GOOD200"]
    universe_sections = [(u, universe_data.get(u, [])) for u in ordered_universes]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(UNIVERSE_SYMBOLS.get(u, [])) for u in ordered_universes},
            "page_title": "India",
        },
    )


@app.get("/us", response_class=HTMLResponse)
def us(request: Request) -> HTMLResponse:
    universes = load_universes_with_prefixes(DATA_DIR, prefixes=["US-"])
    universe_data: Dict[str, List[dict]] = {}
    for universe_name, symbols in universes.items():
        stats = fetch_stats_for_symbols(symbols, max_workers=8, default_suffix=None)
        universe_data[universe_name] = [s.as_dict() for s in stats]
    ordered = sorted(universes.keys())
    universe_sections = [(u, universe_data.get(u, [])) for u in ordered]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(universes.get(u, [])) for u in ordered},
            "page_title": "United States",
        },
    )


@app.get("/germany", response_class=HTMLResponse)
def germany(request: Request) -> HTMLResponse:
    universes = load_universes_with_prefixes(DATA_DIR, prefixes=["GER-"])
    universe_data: Dict[str, List[dict]] = {}
    for universe_name, symbols in universes.items():
        stats = fetch_stats_for_symbols(symbols, max_workers=8, default_suffix="DE")
        universe_data[universe_name] = [s.as_dict() for s in stats]
    ordered = sorted(universes.keys())
    universe_sections = [(u, universe_data.get(u, [])) for u in ordered]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(universes.get(u, [])) for u in ordered},
            "page_title": "Germany",
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


