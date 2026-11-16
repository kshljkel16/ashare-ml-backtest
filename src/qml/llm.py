"""Step 6 — Classify announcement titles with Kimi (provided; adapted from your first project).

The same pattern you built in txn-categoriser: one prompt per batch of titles, a JSON
answer matched back by index, strict validation, a disk cache so a title is paid for once,
and cost accounting. Read it, and be ready to explain each part again.

    sentiment : -1 (likely bad for the share price), 0 (neutral / routine), +1 (likely good)
    event     : one of EVENT_TYPES
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

EVENT_TYPES = {
    "earnings": "periodic reports, earnings results, forecasts or preliminary figures (业绩)",
    "buyback": "share repurchases (回购)",
    "insider_buy": "shareholders or management increasing holdings (增持)",
    "insider_sell": "shareholders or management reducing holdings (减持)",
    "dividend": "dividends and profit distribution (分红/权益分派)",
    "restructuring": "M&A, asset restructuring, spin-offs (并购/重组)",
    "contract": "major contracts, orders, projects, product approvals",
    "financing": "share issuance, convertible bonds, other fund raising (增发/可转债)",
    "penalty": "litigation, regulatory penalties, investigations, risk warnings",
    "pledge": "share pledges and their release (质押)",
    "management": "board, executive or auditor changes",
    "routine": "procedural notices: meeting resolutions, legal opinions, rule changes, other",
}
VALID_SENTIMENT = {-1, 0, 1}

SYSTEM_PROMPT = """You classify Chinese listed-company announcement titles (公告标题) for an equity research team.

For each numbered title return:
- "sentiment": the likely short-term effect on the company's share price for an investor:
  1 = positive, -1 = negative, 0 = neutral or routine. Procedural notices are 0.
- "event": exactly one of these event types:
{event_list}

Examples:
甲公司：关于回购公司股份的进展公告 -> {{"sentiment": 1, "event": "buyback"}}
乙公司：关于控股股东减持股份计划的预披露公告 -> {{"sentiment": -1, "event": "insider_sell"}}
丙公司：2023年年度业绩预增公告 -> {{"sentiment": 1, "event": "earnings"}}
丁公司：关于收到中国证监会立案告知书的公告 -> {{"sentiment": -1, "event": "penalty"}}
戊公司：第八届董事会第十次会议决议公告 -> {{"sentiment": 0, "event": "routine"}}

Respond with ONLY a JSON array, one object per title, in the same order:
[{{"i": 1, "sentiment": 0, "event": "routine"}}, ...]"""


@dataclass
class Label:
    sentiment: int | None      # None = could not be parsed
    event: str | None
    cost_usd: float = 0.0


def build_messages(titles: list[str]) -> tuple[str, str]:
    events = "\n".join(f"  - {k}: {v}" for k, v in EVENT_TYPES.items())
    return (SYSTEM_PROMPT.format(event_list=events),
            "\n".join(f"{i}. {t}" for i, t in enumerate(titles, 1)))


def parse_response(text: str, n: int) -> list[Label]:
    out = [Label(None, None) for _ in range(n)]
    a, b = text.find("["), text.rfind("]")
    if a == -1 or b < a:
        return out
    try:
        items = json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return out
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            pos = int(it["i"]) - 1
            sent = int(it.get("sentiment"))
        except (KeyError, TypeError, ValueError):
            continue
        if not 0 <= pos < n or sent not in VALID_SENTIMENT:
            continue
        event = str(it.get("event", "")).strip().lower()
        out[pos] = Label(sent, event if event in EVENT_TYPES else "routine")
    return out


# ---------------------------------------------------------------------------
@dataclass
class Response:
    text: str
    input_tokens: int
    output_tokens: int


def with_retries(fn: Callable[[], Response], attempts: int = 4) -> Response:
    for k in range(attempts):
        try:
            return fn()
        except Exception:
            if k == attempts - 1:
                raise
            time.sleep(2 ** k)
    raise RuntimeError("unreachable")


class MoonshotClient:
    """Kimi via the OpenAI-compatible API, reasoning switched off (Step 5 of project 1)."""

    def __init__(self) -> None:
        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()
        key = os.getenv("MOONSHOT_API_KEY")
        if not key:
            raise ValueError("MOONSHOT_API_KEY is not set — copy your .env from the first project")
        self.model = os.getenv("MOONSHOT_MODEL", "kimi-k2.6")
        self.client = OpenAI(api_key=key, base_url=os.getenv("MOONSHOT_BASE_URL",
                                                             "https://api.moonshot.cn/v1"))

    def complete(self, system: str, user: str) -> Response:
        def call() -> Response:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_completion_tokens=4000,
                extra_body={"thinking": {"type": "disabled"}},
            )
            return Response(r.choices[0].message.content or "", r.usage.prompt_tokens,
                            r.usage.completion_tokens)
        return with_retries(call)


class TitleClassifier:
    """Batching + disk cache + cost accounting, as in txn-categoriser."""

    def __init__(self, client, batch_size: int = 25, price_in: float = 0.0,
                 price_out: float = 0.0, cache_path: Path | None = None) -> None:
        self.client, self.batch_size = client, batch_size
        self.price_in, self.price_out = price_in, price_out
        self.cache_path = Path(cache_path) if cache_path else None
        self.cache: dict[str, dict] = {}
        if self.cache_path and self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        self.calls = 0

    def classify(self, titles: list[str], progress_every: int = 20) -> list[Label]:
        out: list[Label | None] = [None] * len(titles)
        todo = []
        for i, t in enumerate(titles):
            hit = self.cache.get(t)
            if hit is not None:
                out[i] = Label(hit["sentiment"], hit["event"])
            else:
                todo.append(i)
        for b in range(0, len(todo), self.batch_size):
            pos = todo[b:b + self.batch_size]
            system, user = build_messages([titles[i] for i in pos])
            r = self.client.complete(system, user)
            self.calls += 1
            labels = parse_response(r.text, len(pos))
            cost = (r.input_tokens * self.price_in + r.output_tokens * self.price_out) / 1e6
            for i, lab in zip(pos, labels):
                lab.cost_usd = cost / len(pos)
                out[i] = lab
                if lab.sentiment is not None:
                    self.cache[titles[i]] = {"sentiment": lab.sentiment, "event": lab.event}
            if self.calls % progress_every == 0:
                self.save()
                done = b + len(pos)
                print(f"  classified {done}/{len(todo)} new titles", flush=True)
        self.save()
        return out

    def save(self) -> None:
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
