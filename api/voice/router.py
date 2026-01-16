"""
WebSocket endpoint for real-time voice conversations.
Uses Deepgram Voice Agent API for the full STT → LLM → TTS pipeline.
"""
import logging
import asyncio
import os
import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Customer, Message
from .agent import VoiceAgent
from .tools import VoiceToolExecutor


def format_conversation_history(messages) -> str:
    """Format messages into a string for the voice agent prompt."""
    if not messages:
        return ""

    lines = []
    for msg in messages:
        channel = (msg.channel or "sms").upper()
        if msg.direction == "inbound":
            lines.append(f"Customer [{channel}]: {msg.content}")
        else:
            lines.append(f"Agent [{channel}]: {msg.content}")

    return "\n".join(lines)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for voice conversations using Deepgram Voice Agent.

    Protocol:
    - Client sends: binary audio data (PCM 16-bit, 16kHz)
    - Server sends:
        - JSON messages (transcript, response, tool_call, error)
        - Binary audio data (TTS output)
    """
    await websocket.accept()
    logger.info("[Voice] WebSocket connected")

    # Get API key
    deepgram_key = os.getenv("DEEPGRAM_API_KEY")

    if not deepgram_key:
        await websocket.send_json({
            "type": "error",
            "message": "Voice not configured. Missing DEEPGRAM_API_KEY."
        })
        await websocket.close()
        return

    # Get or create customer - try to link to existing demo customer for cross-channel
    demo_phone = "+15551234567"
    demo_email = "kal@example.com"

    # First check for existing demo customer (from SMS or Email)
    customer = db.query(Customer).filter(
        or_(Customer.phone_number == demo_phone, Customer.email == demo_email)
    ).first()

    if not customer:
        # Create new demo customer with both identifiers
        customer = Customer(
            phone_number=demo_phone,
            email=demo_email,
            first_name="Demo",
            extracted_data={}
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    else:
        # Ensure customer has both identifiers for cross-channel
        updated = False
        if not customer.phone_number:
            customer.phone_number = demo_phone
            updated = True
        if not customer.email:
            customer.email = demo_email
            updated = True
        if updated:
            db.commit()

    # Load conversation history for cross-channel context
    previous_messages = db.query(Message).filter(
        Message.customer_id == customer.id
    ).order_by(Message.created_at).all()

    conversation_history = format_conversation_history(previous_messages)
    if conversation_history:
        logger.info(f"[Voice] Loaded {len(previous_messages)} messages for context")

    # Tool executor
    tool_executor = VoiceToolExecutor(db, customer.id)

    # Callbacks
    async def on_audio(audio_data: bytes):
        """Send TTS audio to browser."""
        try:
            await websocket.send_bytes(audio_data)
        except Exception as e:
            logger.warning(f"[Voice] Error sending audio: {e}")

    async def on_transcript(text: str, is_final: bool):
        """Send transcript to browser."""
        try:
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": is_final,
            })
        except Exception as e:
            logger.warning(f"[Voice] Error sending transcript: {e}")

    async def on_agent_text(text: str):
        """Send agent response text to browser."""
        try:
            await websocket.send_json({
                "type": "response",
                "text": text,
            })
        except Exception as e:
            logger.warning(f"[Voice] Error sending response: {e}")

    async def on_audio_done():
        """Notify browser that TTS audio is complete."""
        try:
            await websocket.send_json({
                "type": "audio_done",
            })
        except Exception as e:
            logger.warning(f"[Voice] Error sending audio_done: {e}")

    def on_function_call(name: str, args: Dict[str, Any]) -> Dict:
        """Execute function call and return result."""
        logger.info(f"[Voice] Function call: {name}({args})")

        # Notify browser
        asyncio.create_task(websocket.send_json({
            "type": "tool_call",
            "name": name,
            "args": args,
        }))

        # Execute tool
        return tool_executor.execute(name, args)

    # Create voice agent with conversation history
    agent = VoiceAgent(
        deepgram_key=deepgram_key,
        on_audio=lambda data: asyncio.create_task(on_audio(data)),
        on_transcript=lambda t, f: asyncio.create_task(on_transcript(t, f)),
        on_agent_text=lambda t: asyncio.create_task(on_agent_text(t)),
        on_function_call=on_function_call,
        on_audio_done=lambda: asyncio.create_task(on_audio_done()),
        conversation_history=conversation_history,
    )

    try:
        # Start agent
        await agent.start()

        # Send ready
        await websocket.send_json({
            "type": "ready",
            "message": "Voice Agent connected"
        })

        # Process incoming audio
        while True:
            data = await websocket.receive()

            # Handle disconnect message
            if data.get("type") == "websocket.disconnect":
                logger.info("[Voice] Received disconnect message")
                break

            if "bytes" in data:
                await agent.send_audio(data["bytes"])

            elif "text" in data:
                msg = json.loads(data["text"])
                if msg.get("type") == "stop":
                    break

    except WebSocketDisconnect:
        logger.info("[Voice] WebSocket disconnected")

    except Exception as e:
        logger.error(f"[Voice] Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        await agent.stop()
        logger.info("[Voice] Session ended")
