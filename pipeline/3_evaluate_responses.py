"""Evaluate raw model outputs using OpenAI Structured Outputs."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.config import get_settings, validate_required_env
from pipeline.db import (
    fetch_raw_responses_for_evaluation,
    get_connection,
    init_db,
    upsert_parsed_metric,
)


class JudgeResult(BaseModel):
    top_brand: str = Field(
        description="Single best brand recommendation from the response."
    )
    sentiment: float = Field(
        ge=-1.0,
        le=1.0,
        description="Sentiment towards the top brand in range [-1.0, 1.0].",
    )
    key_features: list[str] = Field(
        min_length=1,
        description="Distinct product attributes that influenced recommendation.",
    )


def _normalized_brand(top_brand: str) -> str:
    value = (top_brand or "").strip()
    if not value:
        return "Unknown"
    return value


async def _with_retry(
    operation: Callable[[], Any],
    *,
    operation_name: str,
    max_retries: int,
    base_delay: float,
) -> Any:
    for attempt in range(1, max_retries + 1):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 - keep resilient against transient API errors
            if attempt == max_retries:
                raise RuntimeError(
                    f"{operation_name} failed after {max_retries} attempts: {exc}"
                ) from exc

            backoff_seconds = max(base_delay, 0.25) * (2 ** (attempt - 1))
            print(
                f"[retry] {operation_name} attempt {attempt}/{max_retries} failed: {exc}. "
                f"Retrying in {backoff_seconds:.2f}s."
            )
            await asyncio.sleep(backoff_seconds)

    raise RuntimeError(f"{operation_name} exhausted retries unexpectedly.")


async def _judge_response(
    client: AsyncOpenAI, *, model: str, raw_text: str, operation_name: str, retries: int, delay: float
) -> JudgeResult:
    async def _operation() -> JudgeResult:
        parsed_response = await client.beta.chat.completions.parse(
            model=model,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert EV brand analyst. Extract structured metrics "
                        "from the provided model response.\n"
                        "- top_brand: one string, choose from brands mentioned; prefer Tesla/Rivian/Lucid if applicable.\n"
                        "- sentiment: float in [-1.0, 1.0].\n"
                        "- key_features: concise list of recommendation drivers."
                    ),
                },
                {"role": "user", "content": raw_text},
            ],
            response_format=JudgeResult,
        )
        message = parsed_response.choices[0].message
        if getattr(message, "parsed", None) is None:
            raise RuntimeError("Judge response missing parsed payload.")
        return message.parsed

    return await _with_retry(
        _operation,
        operation_name=operation_name,
        max_retries=retries,
        base_delay=delay,
    )


async def run(*, force: bool, limit: int | None) -> None:
    validate_required_env(["OPENAI_API_KEY"])
    settings = get_settings()

    with get_connection(settings.db_path) as conn:
        init_db(conn)
        rows = fetch_raw_responses_for_evaluation(conn, force=force)
        if limit is not None:
            rows = rows[:limit]

        if not rows:
            print("No eligible raw responses found for evaluation.")
            return

        counters: Counter[str] = Counter()
        semaphore = asyncio.Semaphore(settings.max_concurrency)
        db_lock = asyncio.Lock()
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        async def _process_row(row) -> str:
            async with semaphore:
                response_id = int(row["id"])
                raw_text = row["raw_text"]
                if not raw_text:
                    return "skipped"
                try:
                    judged = await _judge_response(
                        client,
                        model=settings.openai_model,
                        raw_text=raw_text,
                        operation_name=f"judge(response_id={response_id})",
                        retries=settings.max_retries,
                        delay=settings.request_delay_seconds,
                    )

                    async with db_lock:
                        upsert_parsed_metric(
                            conn,
                            response_id=response_id,
                            top_brand=_normalized_brand(judged.top_brand),
                            sentiment=float(judged.sentiment),
                            key_features=[feature.strip() for feature in judged.key_features if feature.strip()],
                        )
                    print(f"[ok] evaluated response_id={response_id}")
                    return "success"
                except Exception as exc:  # noqa: BLE001 - log and continue
                    print(f"[error] response_id={response_id}: {exc}")
                    return "error"

        results = await asyncio.gather(*[asyncio.create_task(_process_row(row)) for row in rows])
        for result in results:
            counters[result] += 1

        await client.close()

        print(
            "\nEvaluation complete:\n"
            f"  candidates evaluated: {len(rows)}\n"
            f"  successful parses: {counters['success']}\n"
            f"  failures: {counters['error']}\n"
            f"  skipped: {counters['skipped']}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use gpt-4o-mini as judge to extract structured metrics from raw responses."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-evaluate responses even if parsed metrics already exist.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of responses to evaluate.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(force=args.force, limit=args.limit))
