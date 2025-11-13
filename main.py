from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
    ordered_universes = ["H-SUPER45", "H-GOOD45", "H-GOOD200"]
    india_counts = {u: len(UNIVERSE_SYMBOLS.get(u, [])) for u in ordered_universes}
    us_universes = load_universes_with_prefixes(DATA_DIR, prefixes=["US-"])
    us_count = sum(len(syms) for syms in us_universes.values())
    ger_universes = load_universes_with_prefixes(DATA_DIR, prefixes=["GER-"])
    ger_count = sum(len(syms) for syms in ger_universes.values())
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "total_counts": india_counts,
            "us_count": us_count,
            "ger_count": ger_count,
        },
    )


@app.get("/india", response_class=HTMLResponse)
def india(request: Request) -> HTMLResponse:
    # Only provide metadata; data is fetched client-side with caching
    ordered_universes = ["H-SUPER45", "H-GOOD45", "H-GOOD200"]
    universe_sections = [(u, []) for u in ordered_universes]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(UNIVERSE_SYMBOLS.get(u, [])) for u in ordered_universes},
            "page_title": "India",
            "region": "india",
        },
    )


@app.get("/us", response_class=HTMLResponse)
def us(request: Request) -> HTMLResponse:
    universes = load_universes_with_prefixes(DATA_DIR, prefixes=["US-"])
    ordered = sorted(universes.keys())
    universe_sections = [(u, []) for u in ordered]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(universes.get(u, [])) for u in ordered},
            "page_title": "United States",
            "region": "us",
        },
    )


@app.get("/germany", response_class=HTMLResponse)
def germany(request: Request) -> HTMLResponse:
    universes = load_universes_with_prefixes(DATA_DIR, prefixes=["GER-"])
    ordered = sorted(universes.keys())
    universe_sections = [(u, []) for u in ordered]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "universe_sections": universe_sections,
            "total_counts": {u: len(universes.get(u, [])) for u in ordered},
            "page_title": "Germany",
            "region": "germany",
        },
    )

def _get_symbols_for_universe(region: str, universe: str) -> List[str]:
    if region == "india":
        return UNIVERSE_SYMBOLS.get(universe, [])
    if region == "us":
        data = load_universes_with_prefixes(DATA_DIR, prefixes=["US-"])
        return data.get(universe, [])
    if region == "germany":
        data = load_universes_with_prefixes(DATA_DIR, prefixes=["GER-"])
        return data.get(universe, [])
    return []

def _suffix_for_region(region: str) -> str | None:
    if region == "india":
        return "NS"
    if region == "germany":
        return "DE"
    if region == "us":
        return None
    return None

@app.get("/api/universe")
def api_universe(region: str, universe: str) -> JSONResponse:
    symbols = _get_symbols_for_universe(region, universe)
    default_suffix = _suffix_for_region(region)
    stats = fetch_stats_for_symbols(symbols, max_workers=8, default_suffix=default_suffix)
    payload = [s.as_dict() for s in stats]
    return JSONResponse(payload)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


