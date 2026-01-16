import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests

from config import settings


logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]
    tool_calls: List[ToolCall] = None
    finish_reason: str = "stop"


class OpenRouterClient:
    """Client for OpenRouter API (OpenAI-compatible interface for multiple LLMs)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-sonnet-4.5",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

        if not api_key or not api_key.startswith("sk-or-"):
            logger.warning("OpenRouter API key may be invalid (should start with sk-or-)")

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[List[Dict]] = None,
    ) -> LLMResponse:
        """Send a chat completion request."""
        model = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-support-agent.local",
            "X-Title": "AI Support Agent",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        logger.info(f"Calling OpenRouter with model: {model}")
        if tools:
            logger.info(f"  Tools available: {[t['function']['name'] for t in tools]}")
        logger.debug(f"Messages: {json.dumps(messages, indent=2)}")

        response = requests.post(
            self.BASE_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            response.raise_for_status()

        data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content", "") or ""
        model_used = data.get("model", model)
        usage = data.get("usage", {})
        finish_reason = data["choices"][0].get("finish_reason", "stop")

        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = []
            for tc in message["tool_calls"]:
                args_str = tc["function"]["arguments"]
                try:
                    args = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    args = {}

                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=args,
                ))
            logger.info(f"LLM requested {len(tool_calls)} tool calls: {[tc.name for tc in tool_calls]}")

        logger.info(f"Got response from {model_used}, {usage.get('total_tokens', '?')} tokens, finish: {finish_reason}")

        return LLMResponse(
            content=content,
            model=model_used,
            usage=usage,
            raw_response=data,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    def chat_with_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Send a chat request expecting JSON response."""
        response = self.chat(messages, model=model, temperature=temperature)
        content = response.content.strip()

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {content}")
            raise


def create_client() -> OpenRouterClient:
    """Create an OpenRouter client with settings from config."""
    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
    )
