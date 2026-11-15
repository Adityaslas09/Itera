import json
import logging
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.models.schemas import ParsedPreferences, SMSSimulateResponse
from backend.app.gateway.model_gateway import gateway
from backend.app.prompts.templates import SURVEY_EXTRACTION_SYSTEM_PROMPT
from backend.app.core import metrics

logger = logging.getLogger("itera.sms")

class SMSService:
    """
    Twilio SMS integration and preference parsing pipeline.
    Supports live Twilio SMS dispatch/webhooks as well as a zero-cost interactive simulator.
    """
    def __init__(self):
        self._twilio_client = None

    def _get_twilio_client(self):
        if not self._twilio_client and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        return self._twilio_client

    async def send_sms(self, to_phone: str, message: str) -> str:
        """Send an SMS message via Twilio or mock provider."""
        client = self._get_twilio_client()
        if client and not settings.DEMO_MODE:
            try:
                msg = client.messages.create(
                    to=to_phone,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    body=message
                )
                metrics.SMS_MESSAGES_TOTAL.labels(direction="outbound", status="success").inc()
                return msg.sid
            except Exception as e:
                logger.error(f"Twilio SMS delivery failure to {to_phone}: {e}")
                metrics.SMS_MESSAGES_TOTAL.labels(direction="outbound", status="failed").inc()
                return f"SIMULATED_FAIL_{to_phone}"
        else:
            logger.info(f"[SMS SIMULATOR -> {to_phone}]: {message}")
            metrics.SMS_MESSAGES_TOTAL.labels(direction="outbound", status="success").inc()
            return f"SIMULATED_SID_{abs(hash(to_phone)) % 1000000}"

    async def parse_survey_response(self, raw_text: str) -> ParsedPreferences:
        """
        Invokes the AI Model Gateway to transform conversational SMS text into structured preferences.
        """
        prompt = f"Participant SMS survey response:\n\"\"\"{raw_text}\"\"\"\nExtract structured preferences as JSON."
        try:
            ai_response = await gateway.generate(
                prompt=prompt,
                system_prompt=SURVEY_EXTRACTION_SYSTEM_PROMPT,
                task="survey_extraction",
                temperature=0.2,
                max_tokens=500
            )

            content = ai_response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return ParsedPreferences(
                activities=data.get("activities", []),
                preferred_climate=data.get("preferred_climate"),
                budget_max_usd=float(data["budget_max_usd"]) if data.get("budget_max_usd") else None,
                dietary_restrictions=data.get("dietary_restrictions", []),
                vibe=data.get("vibe"),
                notes=data.get("notes")
            )
        except Exception as e:
            logger.warning(f"AI preference parsing error: {e}. Falling back to heuristic rule-based extraction.")
            # Heuristic fallback
            lower = raw_text.lower()
            return ParsedPreferences(
                activities=[w for w in ["beach", "hiking", "museums", "food", "party", "relaxing"] if w in lower],
                preferred_climate="warm" if "warm" in lower or "beach" in lower or "sun" in lower else "temperate",
                budget_max_usd=1200.0,
                dietary_restrictions=["vegetarian"] if "veg" in lower else [],
                vibe="balanced",
                notes=raw_text
            )

sms_service = SMSService()
