"""Compatibility engine — maps hardware to model recommendations."""

import json
from ..config import CATALOG_PATH


def load_catalog() -> list[dict]:
    with open(CATALOG_PATH) as f:
        return json.load(f)


def check(hardware: dict) -> list[dict]:
    """Return catalog entries with compatibility ratings."""
    ram = hardware.get("ram_gb", 0)
    gpu = hardware.get("gpu") or {}
    vram = gpu.get("vram_gb", 0)
    has_gpu = gpu is not None and gpu.get("name") and not gpu.get("is_integrated", False)

    catalog = load_catalog()
    results = []

    for model in catalog:
        req_ram = model.get("ram_gb", 999)
        req_vram = model.get("vram_gb", 999)

        # Compatibility logic
        if has_gpu and vram >= req_vram and ram >= req_ram:
            rating = "Excellent"
            explanation = f"Your {vram:.0f}GB GPU runs this comfortably."
        elif ram >= req_ram + 4:
            rating = "Good"
            explanation = f"Runs via CPU with your {ram:.0f}GB RAM. May be slower."
        elif ram >= req_ram:
            rating = "CPU Only"
            explanation = f"Tight on RAM ({ram:.0f}GB). Expect slower CPU inference."
        else:
            rating = "Limited"
            explanation = f"Needs {req_ram}GB RAM. You have {ram:.0f}GB."

        results.append({**model, "rating": rating, "explanation": explanation})

    return sorted(results, key=lambda m: (
        {"Excellent": 0, "Good": 1, "CPU Only": 2, "Limited": 3}[m["rating"]],
        -m.get("params_count", 0) if isinstance(m.get("params_count"), (int, float)) else 0
    ))


def get_recommendations(hardware: dict, limit: int = 4) -> list[dict]:
    """Get top recommended models for hardware."""
    compatible = check(hardware)
    excellent = [m for m in compatible if m["rating"] == "Excellent"]
    good = [m for m in compatible if m["rating"] == "Good"]

    picks = []
    # Best overall
    if excellent:
        picks.append({**excellent[0], "recommendation": "⭐ Best Overall"})
    # Best coding (prioritize coding category from excellent, fallback to good)
    coding = [m for m in (excellent + good) if m["category"] == "Coding"]
    if coding:
        picks.append({**coding[0], "recommendation": "💻 Best Coding"})
    # Fastest (smallest excellent model)
    if excellent:
        by_size = sorted(excellent, key=lambda m: m.get("ram_gb", 999))
        if (not picks or by_size[0]["tag"] != picks[0]["tag"]):
            picks.append({**by_size[0], "recommendation": "⚡ Fastest"})
    # Best reasoning (largest excellent or top good)
    reasoning_options = excellent or good
    if reasoning_options:
        by_size = sorted(reasoning_options, key=lambda m: -m.get("ram_gb", 0))
        existing_tags = {p["tag"] for p in picks}
        for m in by_size:
            if m["tag"] not in existing_tags:
                picks.append({**m, "recommendation": "🧠 Best Reasoning"})
                break

    return picks[:limit]
