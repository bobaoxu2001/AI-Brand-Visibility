"""Fetch real LLM responses for all prompts using OpenAI + Anthropic."""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.config import get_settings, validate_required_env
from pipeline.db import fetch_prompts, get_connection, init_db, upsert_raw_response


def _extract_openai_text(response: Any) -> str:
    message_content = response.choices[0].message.content
    if isinstance(message_content, str):
        return message_content.strip()

    parts: list[str] = []
    for part in message_content or []:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _extract_anthropic_text(response: Any) -> str:
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


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
        except Exception as exc:  # noqa: BLE001 - deliberate broad catch for API resilience
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


async def _fetch_openai_response(
    client: AsyncOpenAI, model: str, prompt_text: str
) -> str:
    response = await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an EV purchase advisor. Answer with practical, balanced, "
                    "evidence-oriented guidance."
                ),
            },
            {"role": "user", "content": prompt_text},
        ],
    )
    return _extract_openai_text(response)


async def _fetch_anthropic_response(
    client: AsyncAnthropic, model: str, prompt_text: str
) -> str:
    response = await client.messages.create(
        model=model,
        max_tokens=700,
        temperature=0.2,
        system=(
            "You are an EV purchase advisor. Answer with practical, balanced, "
            "evidence-oriented guidance."
        ),
        messages=[{"role": "user", "content": prompt_text}],
    )
    return _extract_anthropic_text(response)


async def _process_prompt_for_model(
    *,
    prompt_id: int,
    prompt_text: str,
    provider_name: str,
    model_name: str,
    semaphore: asyncio.Semaphore,
    db_lock: asyncio.Lock,
    settings_delay: float,
    settings_retries: int,
    db_conn,
    openai_client: AsyncOpenAI,
    anthropic_client: AsyncAnthropic,
) -> str:
    async with semaphore:
        jitter = random.uniform(0.0, max(0.0, settings_delay / 2))
        await asyncio.sleep(settings_delay + jitter)

        try:
            if provider_name == "openai":
                text = await _with_retry(
                    lambda: _fetch_openai_response(
                        openai_client, model_name, prompt_text
                    ),
                    operation_name=f"openai(prompt_id={prompt_id})",
                    max_retries=settings_retries,
                    base_delay=settings_delay,
                )
            else:
                text = await _with_retry(
                    lambda: _fetch_anthropic_response(
                        anthropic_client, model_name, prompt_text
                    ),
                    operation_name=f"anthropic(prompt_id={prompt_id})",
                    max_retries=settings_retries,
                    base_delay=settings_delay,
                )

            if not text:
                raise RuntimeError("Model returned an empty response.")

            async with db_lock:
                upsert_raw_response(
                    db_conn,
                    prompt_id=prompt_id,
                    model_name=model_name,
                    raw_text=text,
                    status="success",
                    error_message=None,
                )
            print(f"[ok] prompt_id={prompt_id} provider={provider_name}")
            return "success"
        except Exception as exc:  # noqa: BLE001 - keep pipeline resilient
            error_message = str(exc)[:500]
            async with db_lock:
                upsert_raw_response(
                    db_conn,
                    prompt_id=prompt_id,
                    model_name=model_name,
                    raw_text=None,
                    status="error",
                    error_message=error_message,
                )
            print(f"[error] prompt_id={prompt_id} provider={provider_name}: {error_message}")
            return "error"


async def run(limit: int | None, provider_filter: str | None) -> None:
    validate_required_env(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
    settings = get_settings()

    with get_connection(settings.db_path) as conn:
        init_db(conn)
        prompts = fetch_prompts(conn)
        if not prompts:
            raise RuntimeError(
                "No prompts found. Run pipeline/1_generate_prompts.py before fetching responses."
            )
        if limit is not None:
            prompts = prompts[:limit]

        semaphore = asyncio.Semaphore(settings.max_concurrency)
        db_lock = asyncio.Lock()
        counters: Counter[str] = Counter()
        tasks: list[asyncio.Task[str]] = []

        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        provider_specs = []
        if provider_filter in (None, "openai"):
            provider_specs.append(("openai", settings.openai_model))
        if provider_filter in (None, "anthropic"):
            provider_specs.append(("anthropic", settings.anthropic_model))

        for prompt in prompts:
            for provider_name, model_name in provider_specs:
                tasks.append(
                    asyncio.create_task(
                        _process_prompt_for_model(
                            prompt_id=prompt["id"],
                            prompt_text=prompt["prompt_text"],
                            provider_name=provider_name,
                            model_name=model_name,
                            semaphore=semaphore,
                            db_lock=db_lock,
                            settings_delay=settings.request_delay_seconds,
                            settings_retries=settings.max_retries,
                            db_conn=conn,
                            openai_client=openai_client,
                            anthropic_client=anthropic_client,
                        )
                    )
                )

        for result in await asyncio.gather(*tasks):
            counters[result] += 1

        print(
            "\nFetch complete:\n"
            f"  prompts processed: {len(prompts)}\n"
            f"  providers per prompt: {len(provider_specs)}\n"
            f"  successful responses: {counters['success']}\n"
            f"  failed responses: {counters['error']}"
        )

        await openai_client.close()
        await anthropic_client.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch responses from OpenAI and Anthropic for every stored prompt."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional prompt limit for a smaller test run.",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default=None,
        help="Optional single-provider mode.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(limit=args.limit, provider_filter=args.provider))
