import json
from pathlib import Path
from typing import Dict, List, Iterable


UNIVERSE_NAMES = ["H-SUPER45", "H-GOOD45", "H-GOOD200"]


def _read_symbols_from_json(path: Path) -> List[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, dict) and isinstance(data.get("symbols"), list):
        raw = data["symbols"]
    elif isinstance(data, list):
        raw = data
    else:
        return []
    # Normalize and dedupe while preserving order
    seen = set()
    result: List[str] = []
    for s in raw:
        sym = str(s).strip()
        if not sym:
            continue
        if sym not in seen:
            seen.add(sym)
            result.append(sym)
    return result


def load_universes_from_json(data_dir: Path) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for name in UNIVERSE_NAMES:
        file_path = data_dir / f"{name}.json"
        result[name] = _read_symbols_from_json(file_path)
    return result


def load_universes_with_prefixes(data_dir: Path, prefixes: Iterable[str]) -> Dict[str, List[str]]:
    """
    Load all universes whose filenames start with any of the provided prefixes.
    Returns dict of universe_name (from filename without .json) -> symbols.
    """
    result: Dict[str, List[str]] = {}
    if not data_dir.exists():
        return result
    for path in sorted(data_dir.glob("*.json")):
        stem = path.stem  # filename without suffix
        if any(stem.startswith(p) for p in prefixes):
            result[stem] = _read_symbols_from_json(path)
    return result

