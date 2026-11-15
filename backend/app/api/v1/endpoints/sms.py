from fastapi import APIRouter, Form, HTTPException, Response
from typing import Optional
from backend.app.models.schemas import SMSSimulateRequest, SMSSimulateResponse
from backend.app.services.trip_service import trip_service

router = APIRouter()

@router.post("/webhook")
async def twilio_inbound_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: Optional[str] = Form(None)
):
    """
    Standard Twilio Inbound Webhook endpoint.
    Receives incoming SMS messages from participants, parses travel preferences with AI,
    and returns a TwiML response.
    """
    participant = await trip_service.record_participant_survey(
        phone_number=From,
        message_body=Body
    )

    if participant and participant.preferences:
        prefs = participant.preferences
        budget_str = f"${prefs.budget_max_usd:.0f}" if prefs.budget_max_usd else "flexible"
        reply_text = f"PackVote: Thanks {participant.name}! Captured: Budget {budget_str}, Climate {prefs.preferred_climate or 'any'}. We'll notify you when voting begins!"
    else:
        reply_text = "PackVote: Thank you for your response! Your travel preferences have been logged."

    # Return standard Twilio TwiML XML
    xml_content = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_text}</Message></Response>'
    return Response(content=xml_content, media_type="application/xml")

@router.post("/simulate", response_model=SMSSimulateResponse)
async def simulate_sms_survey(payload: SMSSimulateRequest):
    """
    Interactive SMS Simulator endpoint.
    Allows recruiters, developers, and users to simulate replying via SMS to test preference parsing.
    """
    participant = await trip_service.record_participant_survey(
        phone_number=payload.participant_phone,
        message_body=payload.message_body,
        trip_id=payload.trip_id
    )

    if not participant:
        raise HTTPException(status_code=404, detail="Participant or trip not found for specified phone number")

    return SMSSimulateResponse(
        success=True,
        participant_name=participant.name,
        parsed_preferences=participant.preferences,
        confirmation_sms_sent=f"Thanks {participant.name}! Captured your preferences: Budget ${participant.preferences.budget_max_usd if participant.preferences else 'N/A'}"
    )
