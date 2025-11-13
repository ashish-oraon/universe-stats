from pathlib import Path
import json

from parsers.reference_parser import parse_universes


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    md_path = repo_root / "Hemant_Jain_Stock_Lists_Reference.md"
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    universes = parse_universes(md_path)
    for name, symbols in universes.items():
        out_path = data_dir / f"{name}.json"
        payload = {"symbols": symbols}
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {out_path} ({len(symbols)} symbols)")


if __name__ == "__main__":
    main()

