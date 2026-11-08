"""CLI: batch preparation with a manifest."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .core import collect, process

FIELDS = ["source", "output", "width", "height", "bytes", "status"]


def run(args) -> int:
    source = Path(args.input)
    if not source.exists():
        print(f"Vstup nenalezen: {source}", file=sys.stderr)
        return 1

    files = collect(source)
    if not files:
        print("Nenalezeny žádné obrázky.", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    rows, failed = [], 0
    for index, path in enumerate(files, start=1):
        sku = path.stem.split("_")[0]
        name = f"{sku}_{index:02d}.jpg"
        target = out_dir / name
        if args.dry_run:
            rows.append({"source": str(path), "output": str(target), "width": "", "height": "",
                         "bytes": "", "status": "dry-run"})
            continue
        try:
            result = process(path, target, size=args.size, quality=args.quality,
                             threshold=args.threshold)
            status = "ok-padded" if result.padded else "ok"
            rows.append({"source": str(path), "output": str(target),
                         "width": result.width, "height": result.height,
                         "bytes": target.stat().st_size, "status": status})
            print(f"[{status:20}] {path.name} -> {target.name} ({result.width}x{result.height})")
        except Exception as exc:  # noqa: BLE001 - keep batch alive
            failed += 1
            rows.append({"source": str(path), "output": "", "width": "", "height": "",
                         "bytes": "", "status": f"error: {str(exc)[:80]}"})
            print(f"[error               ] {path.name}: {exc}", file=sys.stderr)

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest = out_dir / "manifest.csv"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nManifest: {manifest} | souborů: {len(rows)} | chyb: {failed}")

    return 2 if failed else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="img-batch", description="Dávková příprava produktových fotek")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="Zpracovat složku nebo jeden soubor")
    p.add_argument("--in", dest="input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--size", type=int, default=1600)
    p.add_argument("--quality", type=int, default=90)
    p.add_argument("--threshold", type=int, default=245, help="Práh pozadí (0-255)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
