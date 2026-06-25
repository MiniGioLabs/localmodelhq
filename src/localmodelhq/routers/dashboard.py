"""Dashboard + model management routes."""

import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from ..services.hardware import detect
from ..services.compatibility import check, get_recommendations
from ..services.ollama import get_installed_models, pull_model, delete_model
from ..services.benchmark import run_benchmark, save_results, get_history, get_bests
from ..config import CATALOG_PATH

router = APIRouter()


def _render(request: Request, template: str, **kwargs):
    from ..main import templates
    return templates.TemplateResponse(request, template, {"request": request, **kwargs})


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    hw = await detect()
    catalog = check(hw)
    installed = await get_installed_models()
    installed_tags = {m["name"] for m in installed}
    recommendations = get_recommendations(hw)
    history = await get_history(10)
    bests = await get_bests()

    return _render(request, "dashboard.html",
                   hw=hw, catalog=catalog, installed=installed,
                   installed_tags=installed_tags, recommendations=recommendations,
                   history=history, bests=bests)


@router.post("/models/pull", response_class=HTMLResponse)
async def install_model(request: Request, model_tag: str = Form(...)):
    """Install a model — starts pull and returns progress HTML."""
    return HTMLResponse(
        f'<div id="pull-status-{model_tag.replace(":","-").replace(".","-")}" '
        f'hx-post="/models/pull/progress" hx-vals=\'{{"model_tag":"{model_tag}"}}\' '
        f'hx-trigger="load" hx-swap="innerHTML" '
        f'class="text-xs text-brand animate-pulse">Starting download...</div>'
    )


@router.post("/models/pull/progress", response_class=HTMLResponse)
async def pull_progress(request: Request, model_tag: str = Form(...)):
    """Stream pull progress (returns one chunk per htmx poll)."""
    div_id = f"pull-status-{model_tag.replace(':', '-').replace('.', '-')}"
    try:
        async for status in pull_model(model_tag):
            if "completed" in status:
                # Mark as installed in DB
                from ..database import get_db
                db = await get_db()
                try:
                    await db.execute(
                        "INSERT INTO model_installs (model_tag, model_name) VALUES (?,?)",
                        (model_tag, model_tag)
                    )
                    await db.commit()
                finally:
                    await db.close()
                return HTMLResponse(
                    f'<span id="{div_id}" class="text-xs text-green-600">✅ Installed</span>'
                )
            # Show progress
            pct = status.get("completed", 0) if "completed" in status else status.get("total", 0)
            total = status.get("total", 0)
            if total > 0 and isinstance(pct, (int, float)):
                progress_pct = min(round(pct / total * 100), 99)
                return HTMLResponse(
                    f'<span id="{div_id}" class="text-xs text-brand">'
                    f'⬇ {progress_pct}%</span>'
                )
    except Exception as e:
        return HTMLResponse(
            f'<span id="{div_id}" class="text-xs text-red-500">Error: {str(e)[:50]}</span>'
        )
    return HTMLResponse(f'<span id="{div_id}" class="text-xs text-brand animate-pulse">Downloading...</span>')


@router.post("/models/delete", response_class=HTMLResponse)
async def remove_model(request: Request, model_tag: str = Form(...)):
    ok = await delete_model(model_tag)
    if ok:
        from ..database import get_db
        db = await get_db()
        try:
            await db.execute("DELETE FROM model_installs WHERE model_tag=?", (model_tag,))
            await db.commit()
        finally:
            await db.close()
        return HTMLResponse("🗑 Removed")
    return HTMLResponse("❌ Failed", status_code=500)


@router.post("/models/benchmark", response_class=HTMLResponse)
async def benchmark_model(request: Request, model_tag: str = Form(...), model_name: str = Form(...), category: str = Form("Chat")):
    """Run benchmark and return results HTML."""
    try:
        results = await run_benchmark(model_tag, model_name, category)
        await save_results(results)

        # Build results HTML
        html = '<div class="space-y-2">'
        for r in results:
            if "error" in r:
                html += f'<p class="text-xs text-red-500">{r["category"]}: {r["error"]}</p>'
            else:
                html += (
                    f'<div class="bg-gray-50 rounded-lg p-2 text-xs">'
                    f'<span class="font-medium">{r["category"]}</span>: '
                    f'{r["tokens_per_sec"]} tok/s · '
                    f'{r["duration_ms"]}ms · '
                    f'first token {r["first_token_ms"]}ms'
                    f'</div>'
                )
        html += '</div>'
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f'<p class="text-xs text-red-500">Benchmark failed: {str(e)[:80]}</p>')


@router.get("/hardware/refresh", response_class=HTMLResponse)
async def refresh_hardware(request: Request):
    """Refreshed hardware cards partial."""
    hw = await detect()
    return _render(request, "partials/_hardware.html", hw=hw)
