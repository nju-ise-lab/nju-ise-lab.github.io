#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from migration.generate import DEFAULT_OUTPUT_DIR, generate_site, load_legacy_input, write_site


DEFAULT_INPUT = Path(__file__).resolve().parents[3] / "migration_exports" / "legacy_api"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_inputs(input_dir: Path) -> dict[str, Path]:
    return {path.stem: path for path in sorted(input_dir.glob("*.json"))}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ISE Quick legacy API to Hugo migration skeleton.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--write", action="store_true", help="Write generated files to --output-dir.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_dir = args.input_dir
    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}", file=sys.stderr)
        return 2

    inputs = collect_inputs(input_dir)
    summary_path = inputs.get("summary")
    summary = load_json(summary_path) if summary_path else {}
    site = generate_site(load_legacy_input(input_dir))
    should_write = args.write
    write_summary = write_site(site, args.output_dir) if should_write else None
    print(
        json.dumps(
            {
                "input_dir": str(input_dir),
                "output_dir": str(args.output_dir),
                "json_files": sorted(inputs),
                "resources": sorted((summary.get("resources") or {}).keys()),
                "generated_files": len(site.files),
                "dry_run": not should_write,
                "write": write_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
