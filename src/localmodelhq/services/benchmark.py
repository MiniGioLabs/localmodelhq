"""Benchmark service — runs prompts and stores results."""

from ..database import get_db

BENCHMARK_PROMPTS = {
    "Chat": "Explain quantum computing to a teenager in two paragraphs.",
    "Coding": "Write a Python function to merge overlapping intervals in a list of [start, end] pairs.",
    "Classification": "Classify this support ticket: 'My account was charged twice for the same subscription. Need a refund.' Respond with one word: Billing, Technical, or Account.",
}


async def run_benchmark(model_tag: str, model_name: str, category: str) -> list[dict]:
    """Run all benchmark prompts for a model, return results."""
    from .ollama import generate

    results = []
    for bench_type, prompt in BENCHMARK_PROMPTS.items():
        try:
            result = await generate(model_tag, prompt)
            result["model_tag"] = model_tag
            result["model_name"] = model_name
            result["category"] = bench_type
            result["prompt"] = prompt
            results.append(result)
        except Exception as e:
            results.append({
                "model_tag": model_tag,
                "model_name": model_name,
                "category": bench_type,
                "prompt": prompt,
                "error": str(e),
            })
    return results


async def save_results(results: list[dict]):
    """Persist benchmark results to database."""
    db = await get_db()
    try:
        for r in results:
            if "error" in r:
                continue
            await db.execute(
                """INSERT INTO benchmark_results
                   (model_tag, model_name, category, prompt, response,
                    duration_ms, tokens_per_sec, total_tokens, first_token_ms)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (r["model_tag"], r["model_name"], r["category"], r["prompt"],
                 r.get("response", ""), r.get("duration_ms", 0),
                 r.get("tokens_per_sec", 0), r.get("total_tokens", 0),
                 r.get("first_token_ms", 0))
            )
        await db.commit()
    finally:
        await db.close()


async def get_history(limit: int = 20) -> list[dict]:
    """Get recent benchmark history."""
    db = await get_db()
    try:
        rows = await db.execute(
            """SELECT * FROM benchmark_results
               ORDER BY created_at DESC LIMIT ?""", (limit,)
        )
        return [dict(r) for r in await rows.fetchall()]
    finally:
        await db.close()


async def get_bests() -> dict:
    """Get best performing models across categories."""
    db = await get_db()
    try:
        rows = await db.execute(
            """SELECT model_name, model_tag, category,
                      MIN(duration_ms) as best_duration,
                      MAX(tokens_per_sec) as best_tps
               FROM benchmark_results
               WHERE duration_ms > 0
               GROUP BY model_tag, category
               ORDER BY best_duration ASC"""
        )
        return [dict(r) for r in await rows.fetchall()]
    finally:
        await db.close()
