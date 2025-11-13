import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


HEADING_RE = re.compile(r"^##\s+(.*)")


def _find_sections(markdown_text: str) -> List[Tuple[str, int, int]]:
    lines = markdown_text.splitlines()
    headers: List[Tuple[str, int]] = []
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line.strip())
        if m:
            headers.append((m.group(1).strip(), i))
    sections: List[Tuple[str, int, int]] = []
    for idx, (title, start) in enumerate(headers):
        end = headers[idx + 1][1] if idx + 1 < len(headers) else len(lines)
        sections.append((title, start, end))
    return sections


def _parse_markdown_table(lines: List[str]) -> List[List[str]]:
    rows: List[List[str]] = []
    for line in lines:
        if "|" not in line:
            continue
        if re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(parts)
    return rows


def _extract_symbols_from_table(rows: List[List[str]]) -> List[str]:
    if not rows:
        return []
    header = [c.lower() for c in rows[0]]
    symbol_cols = [i for i, c in enumerate(header) if ("symbol" in c or "ticker" in c or "stock" in c)]
    if not symbol_cols:
        return []
    symbols: List[str] = []
    for r in rows[1:]:
        for idx in symbol_cols:
            if idx < len(r):
                sym = r[idx].strip().strip("`*_ ")
                if not sym or sym.lower() in ("symbol", "ticker"):
                    continue
                # Drop obvious notes in parentheses
                sym = re.sub(r"\(.*?\)", "", sym).strip()
                if sym:
                    symbols.append(sym)
    return symbols


def _extract_symbols_from_inline(text: str) -> List[str]:
    content = " ".join(line.strip() for line in text.splitlines())
    if ":" in content:
        content = content.split(":", 1)[1]
    parts = [p.strip() for p in content.split(",")]
    symbols: List[str] = []
    for p in parts:
        p = re.sub(r"\(.*?\)", "", p).strip()
        p = re.sub(r"[^A-Za-z0-9._\-]+", "", p)
        if p:
            symbols.append(p)
    return symbols


def _extract_symbols_from_block(block_lines: List[str]) -> List[str]:
    # Scan for one or more markdown tables with a header containing Stock/Symbol/Ticker
    idx = 0
    collected: List[str] = []
    n = len(block_lines)
    while idx < n:
        line = block_lines[idx]
        if "|" in line and re.search(r"(Stock|Symbol|Ticker)", line, re.IGNORECASE):
            # collect this table
            table: List[str] = [line]
            idx += 1
            while idx < n and "|" in block_lines[idx]:
                table.append(block_lines[idx])
                idx += 1
            syms = _extract_symbols_from_table(_parse_markdown_table(table))
            collected.extend(syms)
            continue
        idx += 1
    if collected:
        return _dedupe(collected)
    # Fallback: inline comma-separated lists
    return _dedupe(_extract_symbols_from_inline("\n".join(block_lines)))


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for s in items:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _infer_region(section_title: str) -> str:
    t = section_title.lower()
    if "us" in t or "usa" in t or "united states" in t or "american" in t:
        return "US"
    if "germany" in t or "german" in t or "de" == t or t.endswith(" de"):
        return "GER"
    return ""  # unknown/skip


def generate(md_path: Path, out_dir: Path) -> Dict[str, int]:
    text = md_path.read_text(encoding="utf-8")
    sections = _find_sections(text)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: Dict[str, int] = {}
    for title, start, end in sections:
        region = _infer_region(title)
        if not region:
            continue
        block = text.splitlines()[start:end]
        symbols = _extract_symbols_from_block(block)
        if not symbols:
            continue
        # Sanitize filename from title
        safe_title = re.sub(r"[^A-Za-z0-9._\-]+", "_", title).strip("_")
        fname = f"{region}-{safe_title}.json"
        payload = {"symbols": symbols}
        (out_dir / fname).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts[fname] = len(symbols)
    return counts


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    md_path = repo / "Complete_US_German_Hemant_Universe_Classification.md"
    out = repo / "data"
    counts = generate(md_path, out)
    for k, v in sorted(counts.items()):
        print(f"Wrote {k} ({v} symbols)")


if __name__ == "__main__":
    main()

