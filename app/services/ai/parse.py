"""
AI and Heuristic Donation Parsing Service — services/ai/parse.py

Parses unstructured donor text (or photo metadata) into a structured
DonationCreateRequest draft.
Gracefully degrades to regex and keyword heuristics when no LLM key is configured.
"""

import re
from datetime import UTC, datetime, timedelta

import structlog

from app.core.config import DietType, StorageCondition, settings

logger = structlog.get_logger("goldenhour.ai.parse")


def parse_donation_text(
    text: str | None,
    photo_base64: str | None = None,
    now: datetime | None = None,
) -> dict:
    """
    Parse free-form surplus food text into a structured draft dictionary.
    Returns:
    {
        "draft": dict,
        "confidence": float,
        "missing": list[str],
    }
    """
    if now is None:
        now = datetime.now(UTC)

    if not text and not photo_base64:
        return {
            "draft": None,
            "confidence": 0.0,
            "missing": ["items", "diet", "storage", "pickup_window", "pickup"],
        }

    raw = (text or "").lower()

    # 1. Diet Detection
    diet = DietType.VEG
    if any(k in raw for k in ["chicken", "mutton", "fish", "meat", "non veg", "non-veg", "beef", "pork"]):
        diet = DietType.NON_VEG
    elif any(k in raw for k in ["egg", "anda", "omelette", "boiled egg"]):
        diet = DietType.EGG

    # 2. Storage Condition Detection
    storage = StorageCondition.AMBIENT
    if any(k in raw for k in ["hot", "warm", "freshly cooked", "cooked now", "piping hot", "steaming"]):
        storage = StorageCondition.HOT
    elif any(k in raw for k in ["cold", "refrigerated", "chilled", "dairy", "curd", "paneer gravy", "ice cream"]):
        storage = StorageCondition.COLD

    # 3. Portion and Item Detection
    # Look for patterns like "50 portions of biryani", "20 packets dal", "100 meals"
    items = []
    portions_found = None

    qty_patterns = [
        r"(\d+)\s*(?:portions?|meals?|servings?|packets?|plates?|boxes?)\s*(?:of\s*)?([a-zA-Z\s]+?)(?:,|$|\.|\band\b)",
        r"(\d+)\s*kg\s*(?:of\s*)?([a-zA-Z\s]+?)(?:,|$|\.|\band\b)",
        r"([a-zA-Z\s]+?)\s*[-:]\s*(\d+)\s*(?:portions?|meals?|servings?|plates?)",
    ]

    for pat in qty_patterns:
        matches = re.findall(pat, raw)
        for m in matches:
            if m[0].isdigit():
                qty = int(m[0])
                name = m[1].strip()
            else:
                qty = int(m[1])
                name = m[0].strip()

            if name and qty > 0 and len(name) > 2:
                items.append({
                    "name": name.title(),
                    "portions": qty,
                    "weight_kg": round(qty * settings.PORTION_KG, 1),
                })
                if portions_found is None:
                    portions_found = qty
                else:
                    portions_found += qty

    # Fallback if no specific item pattern matched but a number was mentioned
    if not items:
        num_match = re.search(r"(\d+)", raw)
        qty = int(num_match.group(1)) if num_match else 20
        item_name = "Surplus Cooked Meals" if storage == StorageCondition.HOT else "Surplus Food"
        items.append({
            "name": item_name,
            "portions": qty,
            "weight_kg": round(qty * settings.PORTION_KG, 1),
        })
        portions_found = qty

    # 4. Prepared At Estimation
    prepared_at = now - timedelta(hours=1)
    if "2 hour" in raw or "2h" in raw:
        prepared_at = now - timedelta(hours=2)
    elif "just" in raw or "now" in raw:
        prepared_at = now - timedelta(minutes=15)

    # 5. Missing Fields
    missing = []
    missing.append("pickup")  # Donor location needed
    missing.append("pickup_window")  # Explicit pickup window preferred

    confidence = 0.85 if len(items) > 0 and portions_found else 0.50

    draft = {
        "items": items,
        "total_portions": sum(i["portions"] for i in items),
        "diet": diet.value,
        "storage": storage.value,
        "category": "cooked_meals" if storage == StorageCondition.HOT else "packaged_food",
        "prepared_at": prepared_at.isoformat(),
        "pickup_window": {
            "start": now.isoformat(),
            "end": (now + timedelta(hours=2)).isoformat(),
        },
        "notes": text,
    }

    return {
        "draft": draft,
        "confidence": confidence,
        "missing": missing,
    }
