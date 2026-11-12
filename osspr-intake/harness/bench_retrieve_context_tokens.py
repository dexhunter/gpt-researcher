#!/usr/bin/env python3
"""Token count of ChatAgentWithMemory._retrieve_context on a long report."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.pop("TYPESAFE_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)

import tiktoken  # noqa: E402

from backend.chat.chat import ChatAgentWithMemory  # noqa: E402

FIXTURE = ROOT / "deep_agents/benchmark_results/reports_2026-07-04_14-33-21_n8.json"
QUERY = "What are the main competing battery chemistries and their costs per kWh?"
RUNS = 7
# Same encoding the context-filter eval uses to count prompt tokens.
ENCODER = tiktoken.get_encoding("o200k_base")


def long_report() -> str:
    records = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]
    return "\n\n".join(record["gptr"]["report"] for record in records)


def token_count(agent: ChatAgentWithMemory) -> int:
    context = asyncio.run(agent._retrieve_context(QUERY))
    if not context:
        raise SystemExit("empty context")
    return len(ENCODER.encode(context))


def main() -> None:
    os.chdir(ROOT)
    report = long_report()
    agent = ChatAgentWithMemory.__new__(ChatAgentWithMemory)
    agent.report = report
    # Offline default: auto resolves to keyword when no TypeSafe key is set.
    agent.config = SimpleNamespace(context_filter="keyword")
    agent.retriever = None
    token_count(agent)
    samples = [token_count(agent) for _ in range(RUNS)]
    ordered = sorted(samples)
    median = ordered[len(ordered) // 2]
    noise = (max(samples) - min(samples)) / median * 100.0 if median else 0.0
    json.dump(
        {
            "metric": "token_count",
            "samples": samples,
            "median": median,
            "noise_pct": noise,
            "report_chars": len(report),
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
