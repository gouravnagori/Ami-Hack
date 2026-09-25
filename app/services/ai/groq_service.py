"""
Groq AI Service — services/ai/groq_service.py

High-speed LLM service powered by Groq (Llama 3.3 70B & Llama 3.1 8B).
Handles all AI assistance capabilities:
- Surplus donation structured parsing & food safety assessment
- Multi-role AI assistance (Donor, Shelter, Driver, Ops)
- Allocation rationale & explainability
- Graceful heuristic fallbacks when offline or no API key is provided
"""

import json
from datetime import UTC, datetime
from typing import Any

import structlog

from app.core.config import DietType, StorageCondition, settings

logger = structlog.get_logger("goldenhour.ai.groq")


class GroqService:
    def __init__(self):
        self._override_key: str | None = None
        self._active_key: str | None = None
        self._model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        self._fast_model = settings.GROQ_FAST_MODEL or "llama-3.1-8b-instant"
        self._client = None

    def get_model(self) -> str:
        """Dynamically resolve the configured Groq model from env or disk."""
        try:
            from pathlib import Path
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    clean_line = line.strip()
                    if clean_line.startswith("#") or "=" not in clean_line:
                        continue
                    k, v = clean_line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == "GROQ_MODEL" and v:
                        return v
        except Exception:
            pass
        return getattr(settings, "GROQ_MODEL", "") or "qwen/qwen3.8-27b"

    def get_api_key(self) -> str:
        """Dynamically resolve the most up-to-date Groq API key from memory, env, or disk."""
        if self._override_key and self._override_key.strip():
            return self._override_key.strip()

        # Check OS environment
        import os
        for env_var in ("GROQ_API_KEY", "LLM_API_KEY"):
            val = os.environ.get(env_var, "").strip()
            if val:
                return val

        # Check .env file on disk dynamically
        try:
            from pathlib import Path
            env_file = Path(".env")
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    clean_line = line.strip()
                    if clean_line.startswith("#") or "=" not in clean_line:
                        continue
                    k, v = clean_line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in ("GROQ_API_KEY", "LLM_API_KEY") and v:
                        return v
        except Exception:
            pass

        # Fallback to pydantic settings
        return (getattr(settings, "GROQ_API_KEY", "") or getattr(settings, "LLM_API_KEY", "")).strip()

    def set_api_key(self, key: str, persist_to_env: bool = True) -> bool:
        """Set key in runtime memory and optionally write to .env file."""
        clean_key = key.strip()
        self._override_key = clean_key
        self._client = None  # Force re-initialization on next call
        self._active_key = None

        if persist_to_env:
            try:
                from pathlib import Path
                env_file = Path(".env")
                if env_file.exists():
                    lines = env_file.read_text(encoding="utf-8").splitlines()
                    new_lines = []
                    found = False
                    for line in lines:
                        if line.strip().startswith("GROQ_API_KEY="):
                            new_lines.append(f'GROQ_API_KEY="{clean_key}"')
                            found = True
                        else:
                            new_lines.append(line)
                    if not found:
                        new_lines.append(f'GROQ_API_KEY="{clean_key}"')
                    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            except Exception as e:
                logger.warning("groq.persist_env_failed", error=str(e))

        return True

    def _get_client(self):
        key = self.get_api_key()
        if not key:
            return None
        if self._client is None or self._active_key != key:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=key)
                self._active_key = key
                logger.info("groq.client_initialized", model=self._model)
            except Exception as e:
                logger.warning("groq.client_init_failed", error=str(e))
                self._client = None
        return self._client

    @property
    def is_configured(self) -> bool:
        return bool(self.get_api_key())

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are GoldenHour AI, an intelligent surplus food rescue and dispatch assistant.",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> str | dict[str, Any]:
        """
        Execute an LLM chat completion using Groq.
        """
        client = self._get_client()
        chosen_model = model or self.get_model() or "qwen/qwen3.8-27b"

        if not client:
            raise RuntimeError("Groq API key not configured or client unavailable.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await client.chat.completions.create(**kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
                logger.warning("groq.model_fallback", original=chosen_model, fallback="qwen/qwen3.8-27b")
                kwargs["model"] = "qwen/qwen3.8-27b"
                response = await client.chat.completions.create(**kwargs)
            else:
                raise

        raw_text = response.choices[0].message.content or ""

        if json_mode:
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            try:
                return json.loads(clean)
            except Exception:
                start = clean.find("{")
                end = clean.rfind("}")
                if start != -1 and end != -1:
                    return json.loads(clean[start : end + 1])
                raise

        return raw_text

    async def parse_donation(self, text: str, now: datetime | None = None) -> dict[str, Any]:
        """
        Parse free-form surplus food text into structured food rescue parameters using Groq.
        Falls back to rule heuristics if Groq is unavailable.
        """
        if now is None:
            now = datetime.now(UTC)

        if not self.is_configured:
            # Fallback to local heuristic parser
            from app.services.ai.parse import heuristic_parse_donation
            return heuristic_parse_donation(text, now=now)

        system_prompt = """You are GoldenHour's Food Safety and Surplus Parsing AI.
Extract structured surplus food data from donor natural language text according to Indian food safety standards (FSSAI).
Return ONLY a valid JSON object with these keys:
{
  "total_portions": number,
  "diet": "veg" | "egg" | "non_veg",
  "storage": "hot" | "cold" | "ambient",
  "category": "cooked_meals" | "raw_ingredients" | "packaged_goods" | "bakery",
  "safe_hours": number (estimated hours food remains safe to consume, e.g. 2.5 for hot cooked meals, 4.0 for ambient bakery, 6.0 for cold chain),
  "items": [
    {"name": string, "portions": number, "weight_kg": number}
  ],
  "allergens": [string],
  "handling_instructions": string (brief safety advice for driver and recipient)
}
"""
        prompt = f"Extract surplus food details from this donor note:\n\"{text}\""

        try:
            parsed = await self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                model=self._fast_model,
                temperature=0.1,
                json_mode=True,
            )

            if isinstance(parsed, dict) and "total_portions" in parsed:
                # Normalize values
                portions = int(parsed.get("total_portions") or 50)
                diet = parsed.get("diet", "veg").lower()
                if diet not in ["veg", "egg", "non_veg"]:
                    diet = "veg"
                storage = parsed.get("storage", "ambient").lower()
                if storage not in ["hot", "cold", "ambient"]:
                    storage = "hot" if "hot" in text.lower() else "ambient"

                safe_hours = float(parsed.get("safe_hours") or 2.5)

                items = parsed.get("items") or [
                    {
                        "name": text[:40].strip() or "Surplus Food",
                        "portions": portions,
                        "weight_kg": round(portions * settings.PORTION_KG, 1),
                    }
                ]

                return {
                    "draft": {
                        "total_portions": portions,
                        "diet": diet,
                        "storage": storage,
                        "category": parsed.get("category", "cooked_meals"),
                        "safe_hours": safe_hours,
                        "items": items,
                        "allergens": parsed.get("allergens", []),
                        "handling_instructions": parsed.get("handling_instructions", "Keep covered during transport."),
                    },
                    "confidence": 0.95,
                    "model": self._fast_model,
                    "powered_by": "Groq AI (Llama 3.1)",
                }
        except Exception as e:
            logger.warning("groq.parse_failed_fallback_heuristic", error=str(e))

        from app.services.ai.parse import heuristic_parse_donation
        return heuristic_parse_donation(text, now=now)

    async def assist(
        self,
        role: str,
        query: str,
        user_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Multi-role AI assistant for GoldenHour participants:
        - Donors: Packaging, tax exemption (80G), FSSAI food donation guidelines.
        - Shelters: Capacity planning, intake scheduling, meal distribution.
        - Drivers: Delivery protocols, cold chain maintenance, route guidance.
        - Ops: Bottleneck analysis, urgent escalations, allocation review.
        """
        if not self.is_configured:
            return self._heuristic_assist(role, query, user_name, context)

        role_prompts = {
            "donor": (
                "You are the GoldenHour Food Donor AI Assistant. Help restaurants, caterers, and food businesses "
                "with food packaging standards, safe temperature holding (above 60°C for hot, below 5°C for cold), "
                "FSSAI surplus donation guidelines, and 80G tax benefit calculation."
            ),
            "recipient": (
                "You are the GoldenHour Shelter Intake AI Assistant. Help shelters, orphanages, and NGOs "
                "with meal capacity planning, dietary segregation (pure veg vs non-veg), portion distribution, "
                "and hygienic storage."
            ),
            "driver": (
                "You are the GoldenHour Logistics AI Copilot. Assist rescue drivers with rapid transit safety, "
                "insulated cold-box temperature monitoring, OTP verification steps, and traffic management in Jaipur."
            ),
            "admin": (
                "You are the GoldenHour Central Operations AI Analyst. Help dispatch controllers optimize "
                "hyper-local food routing, minimize spoilage risk, track driver utilization, and resolve bottlenecked allocations."
            ),
        }

        system_prompt = role_prompts.get(
            role.lower(),
            "You are GoldenHour AI, an intelligent assistant for surplus food rescue.",
        )
        system_prompt += (
            "\nProvide concise, practical, highly actionable guidance in clear, friendly language. "
            "Use bullet points where appropriate."
        )

        context_str = json.dumps(context or {}, indent=2) if context else "None"
        prompt = (
            f"User Role: {role.upper()}\n"
            f"User Name: {user_name or 'Participant'}\n"
            f"Current Context: {context_str}\n\n"
            f"User Question: {query}\n\n"
            "Please provide a helpful and direct response:"
        )

        try:
            reply = await self.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                model=self._model,
                temperature=0.3,
                max_tokens=600,
            )
            return {
                "reply": str(reply).strip(),
                "role": role,
                "model": self._model,
                "powered_by": "Groq AI (Llama 3.3 70B)",
            }
        except Exception as e:
            logger.warning("groq.assist_fallback", error=str(e))
            return self._heuristic_assist(role, query, user_name, context)

    def _heuristic_assist(
        self,
        role: str,
        query: str,
        user_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Rule-based smart response when Groq API key is not yet set."""
        q = query.lower()

        if "tax" in q or "80g" in q:
            reply = (
                "Under Section 80G of the Income Tax Act in India, authorized food donations to registered charitable NGOs "
                "qualify for tax deduction certificates. GoldenHour generates verified digital donation receipts automatically "
                "for all successfully delivered meals showing portion counts, verified timestamp, and recipient shelter NGO registration."
            )
        elif "pack" in q or "container" in q or "hot" in q or "temp" in q:
            reply = (
                "Food Safety Guidelines (FSSAI):\n"
                "• Hot food must be sealed in thermal insulated containers and kept above 60°C until pickup.\n"
                "• Cold perishables (dairy, paneer) must be stored at or below 5°C.\n"
                "• Seal containers with tamper-evident tape or clean lids before driver handover.\n"
                "• GoldenHour algorithm prioritizes pickups within 45 minutes of preparation."
            )
        elif "capacity" in q or "intake" in q or "shelter" in q:
            reply = (
                "Shelter Intake Assistance:\n"
                "• Update your intake status in 'Capacity Manager' to let nearby kitchens know your meal needs.\n"
                "• Portions are matched strictly based on your dietary preference (Pure Veg vs Non-Veg).\n"
                "• Deliveries are coordinated to arrive at least 30 minutes before meal times."
            )
        elif "driver" in q or "route" in q or "otp" in q:
            reply = (
                "Driver Logistics Guide:\n"
                "• Confirm pickup using the 4-digit Pickup OTP provided by the kitchen.\n"
                "• Deliver with insulated bags or cold boxes to maintain food safety.\n"
                "• Obtain the Drop-off OTP from the shelter manager upon safe delivery to complete the mission."
            )
        else:
            reply = (
                f"Hello {user_name or 'Partner'}! GoldenHour AI is here to help coordinate food rescues in Jaipur. "
                "You can ask about food safety rules, pickup scheduling, 80G tax receipts, packaging protocols, "
                "or driver arrival estimates."
            )

        return {
            "reply": reply,
            "role": role,
            "model": "rule-based-assistant",
            "powered_by": "GoldenHour Intelligence (Configure GROQ_API_KEY in .env for Llama 3.3)",
        }


# Global Groq service instance
groq_service = GroqService()
