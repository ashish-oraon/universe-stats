import re
from pathlib import Path
from typing import Dict, List, Tuple


HEADING_PATTERN = re.compile(r"^##\s+.*?(H-SUPER45|H-GOOD45|H-GOOD200)\b", re.IGNORECASE)


def _find_sections(markdown_text: str) -> Dict[str, Tuple[int, int]]:
    """
    Locate sections for H-SUPER45, H-GOOD45, H-GOOD200 by heading bounds.
    Returns dict of universe -> (start_index, end_index) line indices (inclusive, exclusive).
    """
    lines = markdown_text.splitlines()
    headings: List[Tuple[str, int]] = []
    for idx, line in enumerate(lines):
        m = HEADING_PATTERN.match(line.strip())
        if m:
            universe = m.group(1).upper()
            headings.append((universe, idx))
    sections: Dict[str, Tuple[int, int]] = {}
    for i, (universe, start) in enumerate(headings):
        end = headings[i + 1][1] if i + 1 < len(headings) else len(lines)
        sections[universe] = (start, end)
    return sections


def _parse_markdown_table(lines: List[str]) -> List[List[str]]:
    """
    Parse a markdown table block into rows of cells (trimmed), excluding header separator line.
    """
    rows: List[List[str]] = []
    for line in lines:
        if "|" not in line:
            continue
        # skip header separator like |---|----|
        if re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue
        # split respecting markdown table style
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(parts)
    return rows


def _extract_symbols_from_table(rows: List[List[str]]) -> List[str]:
    """
    Extract symbols from tables where a column is named 'NSE Symbol'.
    Handles tables with repeated (#, NSE Symbol) pairs across columns (e.g., 8 columns).
    """
    if not rows:
        return []
    header = [c.lower() for c in rows[0]]
    # Identify columns labeled NSE Symbol (can appear multiple times)
    symbol_col_indices = [i for i, c in enumerate(header) if "nse symbol" in c]
    if not symbol_col_indices:
        return []
    symbols: List[str] = []
    for r in rows[1:]:
        for idx in symbol_col_indices:
            if idx < len(r):
                sym = r[idx].strip()
                if not sym or sym.startswith("*(") or sym.startswith("*Total"):
                    continue
                # ignore placeholder ranges like "194-200+ | *(See notes)*"
                if re.search(r"\(\s*See notes\s*\)", sym, re.IGNORECASE):
                    continue
                # strip any non-ticker decorations
                sym = sym.strip("`*_ ")
                if sym and sym.upper() != "NSE SYMBOL":
                    symbols.append(sym)
    return symbols


def _extract_symbols_from_inline_list(text_block: str) -> List[str]:
    """
    Extract symbols from a comma-separated inline list (e.g., 'CHOLAFIN, HEROMOTOCO, ...').
    """
    # Replace newlines with space to treat it continuously
    content = " ".join(line.strip() for line in text_block.splitlines())
    # Part after colon if present
    if ":" in content:
        content = content.split(":", 1)[1]
    parts = [p.strip() for p in content.split(",")]
    symbols: List[str] = []
    for p in parts:
        # remove trailing notes in parentheses
        p = re.sub(r"\(.*?\)", "", p).strip()
        # remove stray non-alnum/-/_ characters
        p = re.sub(r"[^A-Z0-9\-\_\.]+", "", p, flags=re.IGNORECASE)
        if p:
            symbols.append(p)
    return symbols


def parse_universes(markdown_path: Path) -> Dict[str, List[str]]:
    """
    Parse the MD file and return a dict with keys: H-SUPER45, H-GOOD45, H-GOOD200
    Each maps to a list of NSE symbols (as-is from document), deduplicated preserving order.
    """
    text = markdown_path.read_text(encoding="utf-8")
    sections = _find_sections(text)
    lines = text.splitlines()
    result: Dict[str, List[str]] = {"H-SUPER45": [], "H-GOOD45": [], "H-GOOD200": []}
    for universe, (start, end) in sections.items():
        block = lines[start:end]
        # Collect all table-like lines
        table_lines: List[str] = []
        collect_table = False
        for line in block:
            if "|" in line and ("NSE Symbol" in line or collect_table):
                table_lines.append(line)
                collect_table = True
                # stop table when we hit a non-table section
                continue
            if collect_table and "|" not in line:
                # end of table
                break
        symbols = _extract_symbols_from_table(_parse_markdown_table(table_lines))
        # For H-GOOD200, also parse 'Continued' and 'Additional stocks'
        if universe.upper() == "H-GOOD200":
            extra_symbols: List[str] = []
            # Find 'Continued' and 'Additional stocks' paragraphs within block
            joined = "\n".join(block)
            cont_match = re.search(r"\*\*Continued[^\n]*\*\*:(.*?)(?:\n\s*\n|$)", joined, re.DOTALL | re.IGNORECASE)
            if cont_match:
                extra_symbols.extend(_extract_symbols_from_inline_list(cont_match.group(1)))
            add_match = re.search(r"\*\*Additional stocks:\*\*(.*?)(?:\n\s*\n|$)", joined, re.DOTALL | re.IGNORECASE)
            if add_match:
                extra_symbols.extend(_extract_symbols_from_inline_list(add_match.group(1)))
            symbols.extend(extra_symbols)
        # Deduplicate preserving order
        seen = set()
        deduped: List[str] = []
        for s in symbols:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        result[universe.upper()] = deduped
    return result


def main() -> None:
    # Manual test helper
    md_path = Path(__file__).resolve().parents[2] / "Hemant_Jain_Stock_Lists_Reference.md"
    universes = parse_universes(md_path)
    for name, syms in universes.items():
        print(f"{name}: {len(syms)} symbols")
        print(", ".join(syms[:30]), "...")


if __name__ == "__main__":
    main()


