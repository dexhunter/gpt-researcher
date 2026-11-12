#!/usr/bin/env python3
"""Wall time of backend.utils.write_md_to_pdf on one real research report."""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.utils import write_md_to_pdf  # noqa: E402

FIXTURE = ROOT / "deep_agents/benchmark_results/reports_2026-07-04_14-33-21_n8.json"
RUNS = 7


def longest_report() -> str:
    records = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]
    return max((record["gptr"]["report"] for record in records), key=len)


def export_ms(text: str, filename: str) -> float:
    buffer = io.StringIO()
    started = time.perf_counter()
    with contextlib.redirect_stdout(buffer):
        encoded = asyncio.run(write_md_to_pdf(text, filename=filename))
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if not encoded:
        raise SystemExit("write_md_to_pdf returned no file")
    path = Path(unquote(encoded))
    if not path.is_file() or path.stat().st_size <= 0:
        raise SystemExit(f"missing pdf {path}")
    return elapsed_ms


def main() -> None:
    os.chdir(ROOT)
    text = longest_report()
    export_ms(text, "intake-pdf-warmup")
    samples = [export_ms(text, f"intake-pdf-{i}") for i in range(RUNS)]
    ordered = sorted(samples)
    median = ordered[len(ordered) // 2]
    noise = (max(samples) - min(samples)) / median * 100.0
    json.dump(
        {
            "metric": "runtime_ms",
            "samples": samples,
            "median": median,
            "noise_pct": noise,
            "report_chars": len(text),
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
