"""
Deepgram Voice Agent client.
Uses the Voice Agent API which handles STT → LLM → TTS in one connection.
"""
import json
import logging
import asyncio
from typing import Callable, Dict, Any

from deepgram import AsyncDeepgramClient

logger = logging.getLogger(__name__)


def get_system_prompt(conversation_history: str = "") -> str:
    """System prompt for voice conversations."""
    base_prompt = """You are a voice support agent for Macrocenter PC Parts, an online PC components retailer.

VOICE STYLE:
- Short sentences, under 15 words each
- Speak naturally, no bullet points
- Say numbers clearly: "fifteen hundred dollars" not "$1,500"
- Confirm actions: "Done", "Got it", "Let me check"
- One question at a time

SENDING FOLLOW-UPS:
When customers need something in writing (return label, order details, confirmation), use send_followup to email or text them:
- "I'll email you that return label right now"
- "Let me text you the tracking number"

TOOLS:
- lookup_order: Get order details
- check_inventory: Check stock
- process_refund: Issue refunds (auto-escalates over $500)
- create_return_label: Generate return label
- send_followup: Send email or SMS to customer
- escalate_to_human: Transfer to human

Be helpful and efficient. This is a real phone call."""

    if conversation_history:
        return f"""{base_prompt}

PREVIOUS CONVERSATION WITH THIS CUSTOMER (from email/SMS):
{conversation_history}

Use this context! If they mention something from earlier, acknowledge it: "I see you emailed about that RTX 4090 earlier." """

    return base_prompt


def get_function_definitions() -> list:
    """Get function definitions for the voice agent."""
    return [
        {
            "name": "lookup_order",
            "description": "Look up order details by order number",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number (e.g., ORD-1001 or just 1001)"
                    }
                },
                "required": ["order_number"]
            }
        },
        {
            "name": "check_inventory",
            "description": "Check if a product is in stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name or SKU of the product"
                    }
                },
                "required": ["product_name"]
            }
        },
        {
            "name": "process_refund",
            "description": "Issue a refund for an order. Auto-escalates for amounts over $500.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number to refund"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason: customer_request, item_damaged, wrong_item, item_not_received"
                    }
                },
                "required": ["order_number", "reason"]
            }
        },
        {
            "name": "create_return_label",
            "description": "Generate a return shipping label for an order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number for the return"
                    }
                },
                "required": ["order_number"]
            }
        },
        {
            "name": "search_knowledge_base",
            "description": "Search help articles for product info, compatibility, or troubleshooting",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "send_followup",
            "description": "Send a follow-up message to the customer via email or SMS. Use when they need written confirmation or something to reference later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "enum": ["email", "sms"],
                        "description": "Channel to send on: 'email' or 'sms'"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message content to send"
                    }
                },
                "required": ["channel", "message"]
            }
        },
        {
            "name": "escalate_to_human",
            "description": "Transfer the customer to a human agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation"
                    }
                },
                "required": ["reason"]
            }
        },
    ]


class VoiceAgent:
    """
    Deepgram Voice Agent that handles the full conversation pipeline.
    STT (Flux) → LLM (Gemini) → TTS (Aura-2)
    """

    def __init__(
        self,
        deepgram_key: str,
        on_audio: Callable[[bytes], None],
        on_transcript: Callable[[str, bool], None],
        on_agent_text: Callable[[str], None],
        on_function_call: Callable[[str, Dict], Dict],
        on_audio_done: Callable[[], None] = None,
        conversation_history: str = "",
    ):
        self.deepgram_key = deepgram_key
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_agent_text = on_agent_text
        self.on_function_call = on_function_call
        self.on_audio_done = on_audio_done
        self.conversation_history = conversation_history

        self.client = AsyncDeepgramClient(api_key=deepgram_key)
        self._websocket = None
        self._context = None
        self._running = False
        self._listener_task = None

    def _build_settings(self) -> dict:
        """Build the agent settings."""
        # Build greeting based on whether we have history
        if self.conversation_history:
            greeting = "Hi! I can see we've been chatting over email or text. How can I help you on the phone today?"
        else:
            greeting = "Hi! I'm the Macrocenter support assistant. How can I help you today?"

        return {
            "type": "Settings",
            "audio": {
                "input": {
                    "encoding": "linear16",
                    "sample_rate": 16000
                },
                "output": {
                    "encoding": "linear16",
                    "sample_rate": 24000,
                    "container": "none"
                }
            },
            "agent": {
                "listen": {
                    "provider": {
                        "type": "deepgram",
                        "version": "v2",
                        "model": "flux-general-en"
                    }
                },
                "think": {
                    "provider": {
                        "type": "google",
                        "model": "gemini-2.5-flash"
                    },
                    "prompt": get_system_prompt(self.conversation_history),
                    "functions": get_function_definitions()
                },
                "speak": {
                    "provider": {
                        "type": "deepgram",
                        "model": "aura-2-theia-en"
                    }
                },
                "greeting": greeting
            }
        }

    async def _listen_loop(self):
        """Listen for messages from Deepgram (custom loop to handle all message types)."""
        try:
            async for message in self._websocket:
                if not self._running:
                    break

                if isinstance(message, bytes):
                    # TTS audio data
                    self.on_audio(message)
                else:
                    # JSON message
                    try:
                        data = json.loads(message)
                        self._handle_json_message(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"[Agent] Failed to parse message: {e}")

        except Exception as e:
            if self._running:
                logger.error(f"[Agent] Listen loop error: {e}")

    def _handle_json_message(self, data: dict):
        """Handle a JSON message from Deepgram."""
        msg_type = data.get("type", "")

        if msg_type == "Welcome":
            logger.info(f"[Agent] Welcome received (request_id: {data.get('request_id')})")

        elif msg_type == "SettingsApplied":
            logger.info("[Agent] Settings applied")

        elif msg_type == "ConversationText":
            role = data.get("role", "")
            content = data.get("content", "")
            if role == "user":
                self.on_transcript(content, True)
            elif role == "assistant":
                self.on_agent_text(content)

        elif msg_type == "UserStartedSpeaking":
            logger.debug("[Agent] User started speaking")

        elif msg_type == "AgentThinking":
            logger.debug("[Agent] Agent thinking")

        elif msg_type == "AgentStartedSpeaking":
            logger.debug("[Agent] Agent started speaking")

        elif msg_type == "AgentAudioDone":
            logger.debug("[Agent] Agent audio done")
            if self.on_audio_done:
                self.on_audio_done()

        elif msg_type == "FunctionCallRequest":
            self._handle_function_call(data)

        elif msg_type == "Error":
            logger.error(f"[Agent] Error: {data.get('description')} ({data.get('code')})")

        elif msg_type == "Warning":
            logger.warning(f"[Agent] Warning: {data.get('description')}")

        elif msg_type == "History":
            # Ignore history messages (they duplicate ConversationText)
            pass

        else:
            logger.debug(f"[Agent] Unknown message type: {msg_type}")

    def _handle_function_call(self, data: dict):
        """Handle a function call request."""
        try:
            functions = data.get("functions", [])
            for func in functions:
                name = func.get("name", "")
                args = func.get("arguments", {})
                call_id = func.get("id", "")

                logger.info(f"[Agent] Function call: {name}({args}) id={call_id}")

                # Execute the function
                result = self.on_function_call(name, args)
                logger.info(f"[Agent] Function result: {result}")

                # Send response back - note: field is "function_call_id" per Deepgram docs
                response = {
                    "type": "FunctionCallResponse",
                    "function_call_id": call_id,
                    "output": json.dumps(result)
                }
                logger.info(f"[Agent] Sending function response: {response}")
                asyncio.create_task(self._send_function_response(response))

        except Exception as e:
            logger.error(f"[Agent] Function call error: {e}", exc_info=True)

    async def _send_function_response(self, response: dict):
        """Send function call response with error handling."""
        try:
            if self._websocket and self._running:
                await self._websocket.send(json.dumps(response))
                logger.info("[Agent] Function response sent successfully")
            else:
                logger.warning("[Agent] WebSocket not available for function response")
        except Exception as e:
            logger.error(f"[Agent] Failed to send function response: {e}")

    async def start(self):
        """Start the voice agent connection."""
        self._running = True

        try:
            # Connect using SDK (to get proper auth headers)
            self._context = self.client.agent.v1.connect()
            connection = await self._context.__aenter__()
            self._websocket = connection._websocket

            # Start our custom listener (not SDK's start_listening which fails on unknown types)
            self._listener_task = asyncio.create_task(self._listen_loop())

            # Send settings
            settings = self._build_settings()
            await self._websocket.send(json.dumps(settings))

            logger.info("[Agent] Voice Agent started")

        except Exception as e:
            logger.error(f"[Agent] Failed to start: {e}")
            raise

    async def send_audio(self, audio_data: bytes):
        """Send audio data to the agent."""
        if self._websocket and self._running:
            try:
                await self._websocket.send(audio_data)
            except Exception as e:
                logger.warning(f"[Agent] Error sending audio: {e}")

    async def stop(self):
        """Stop the voice agent."""
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._context:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception as e:
                logger.debug(f"[Agent] Context cleanup: {e}")

        logger.info("[Agent] Voice Agent stopped")
