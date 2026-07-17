"""Download migrated image references into a Hugo site tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlsplit, urlunsplit, quote
from urllib.request import Request, urlopen


SCRIPT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=SCRIPT_ROOT / "output",
        help="Hugo site directory containing data/media-manifest.json",
    )
    parser.add_argument("--force", action="store_true", help="redownload existing files")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    site_dir = args.site_dir.resolve()
    manifest_path = site_dir / "data" / "media-manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    downloaded = 0
    rewritten = 0
    failures: list[str] = []

    seen: set[tuple[str, Path]] = set()
    for entry in entries:
        source_url = (entry.get("source_url") or "").strip()
        suggested = entry.get("suggested_path") or ""
        if not source_url or not suggested:
            continue

        destination = _destination(site_dir, suggested)
        key = (source_url, destination)
        if key in seen:
            continue
        seen.add(key)

        try:
            if args.force or not destination.exists():
                _download(source_url, destination, timeout=args.timeout)
                downloaded += 1
            if entry.get("field") == "body":
                page = destination.parent / "index.md"
                if page.exists():
                    content = page.read_text(encoding="utf-8")
                    if source_url in content:
                        page.write_text(content.replace(source_url, destination.name), encoding="utf-8")
                        rewritten += 1
        except Exception as exc:  # noqa: BLE001 - report all remote media failures together
            failures.append(f"{source_url} -> {destination}: {exc}")

    print(f"downloaded={downloaded} body_pages_rewritten={rewritten}")
    if failures:
        print("failed media:")
        print("\n".join(failures))
        return 1
    return 0


def _destination(site_dir: Path, suggested: str) -> Path:
    path = Path(suggested)
    if suggested.startswith("media/slides/"):
        return site_dir / "static" / "images" / "slides" / path.name
    return site_dir / path


def _download(url: str, destination: Path, *, timeout: int) -> None:
    parsed = urlsplit(url)
    safe_url = urlunsplit(
        (parsed.scheme, parsed.netloc, quote(parsed.path, safe="/%:@"), parsed.query, parsed.fragment)
    )
    request = Request(safe_url, headers={"User-Agent": "ise-quick-media-localizer/1.0"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - URLs come from migration input
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
            shutil.copyfileobj(response, temporary)
            temporary_path = Path(temporary.name)
    temporary_path.replace(destination)


if __name__ == "__main__":
    raise SystemExit(main())
