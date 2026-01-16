import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from llm.openrouter_client import OpenRouterClient, create_client
from conversation.prompts import (
    AGENT_SYSTEM_PROMPT,
    format_conversation_history,
    format_customer_data,
)
from conversation.tools import TOOL_DEFINITIONS, ToolExecutor


logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """Record of a tool call made during conversation."""
    id: str
    name: str
    args: Dict[str, Any]
    result: Dict[str, Any]


@dataclass
class ConversationResult:
    """Result of processing a conversation turn."""
    response_text: str
    extracted_data: Dict[str, Any]  # JSONB data (issue_type, severity, product)
    column_data: Dict[str, Any]  # Dedicated column data (first_name, company_name)
    tool_calls: List[ToolCallRecord]  # Tool calls made during this turn


class ConversationEngine:
    """Orchestrates the conversation flow using LLM with tool calling."""

    def __init__(self, client: Optional[OpenRouterClient] = None):
        self.client = client or create_client()
        logger.info(f"ConversationEngine initialized with model: {self.client.model}")

    def process_turn(
        self,
        customer_data: Dict[str, Any],
        messages: List[Dict],
        articles: List[Dict],
        customer_id: Optional[int] = None,
        orders: Optional[List[Dict]] = None,
        products: Optional[List[Dict]] = None,
        inventory: Optional[List[Dict]] = None,
    ) -> ConversationResult:
        """Process a conversation turn with the agent."""
        logger.info("=" * 50)
        logger.info("Processing conversation turn")
        logger.info(f"  Existing customer data: {customer_data}")
        logger.info(f"  Messages in history: {len(messages)}")
        logger.info(f"  Available KB articles: {len(articles)}")

        logger.info("Agent generating response...")
        response_text, updated_data, column_data, tool_calls = self._generate_response(
            messages=messages,
            customer_data=customer_data,
            articles=articles,
            customer_id=customer_id,
            orders=orders or [],
            products=products or [],
            inventory=inventory or [],
        )
        logger.info(f"  Response: {response_text[:100]}...")
        logger.info(f"  Updated JSONB data: {updated_data}")
        logger.info(f"  Updated column data: {column_data}")
        logger.info(f"  Tool calls made: {len(tool_calls)}")

        logger.info("=" * 50)

        return ConversationResult(
            response_text=response_text,
            extracted_data=updated_data,
            column_data=column_data,
            tool_calls=tool_calls,
        )

    def _generate_response(
        self,
        messages: List[Dict],
        customer_data: Dict[str, Any],
        articles: List[Dict],
        customer_id: Optional[int] = None,
        orders: Optional[List[Dict]] = None,
        products: Optional[List[Dict]] = None,
        inventory: Optional[List[Dict]] = None,
    ) -> tuple[str, Dict[str, Any], Dict[str, Any], List[ToolCallRecord]]:
        """Generate the agent's response using LLM with tools."""
        # Format conversation history and customer data for context
        formatted_history = format_conversation_history(messages)
        formatted_customer = format_customer_data(customer_data)

        # Build the prompt for the LLM
        prompt = f"""Continue this conversation with the customer.

CONVERSATION HISTORY:
{formatted_history}

WHAT WE KNOW ABOUT THE CUSTOMER:
{formatted_customer}

Based on this context, respond appropriately. You have tools available if needed.
Use lookup_order when an order number is mentioned. Use save_customer_info when the customer shares new information."""

        # Build messages for the LLM
        llm_messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        # Create tool executor with all data sources
        tool_executor = ToolExecutor(
            articles=articles,
            orders=orders or [],
            products=products or [],
            inventory=inventory or [],
            customer_id=customer_id,
            existing_customer_data=customer_data,
        )

        # Make the initial LLM call with tools
        response = self.client.chat(llm_messages, tools=TOOL_DEFINITIONS)

        # Track all tool calls made during this turn
        tool_call_records: List[ToolCallRecord] = []

        # Handle tool calls in a loop (agent may call multiple tools)
        max_iterations = 5
        iteration = 0

        while response.tool_calls and iteration < max_iterations:
            iteration += 1
            logger.info(f"Tool calling iteration {iteration}")

            # Add assistant message with tool calls
            assistant_msg = {"role": "assistant", "content": response.content or ""}
            if response.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        }
                    }
                    for tc in response.tool_calls
                ]
            llm_messages.append(assistant_msg)

            # Execute each tool and add results
            for tool_call in response.tool_calls:
                logger.info(f"Executing tool: {tool_call.name}")
                result = tool_executor.execute(tool_call.name, tool_call.arguments)

                # Record the tool call
                tool_call_records.append(ToolCallRecord(
                    id=tool_call.id,
                    name=tool_call.name,
                    args=tool_call.arguments,
                    result=result,
                ))

                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            # Call LLM again with tool results
            response = self.client.chat(llm_messages, tools=TOOL_DEFINITIONS)

        if iteration >= max_iterations:
            logger.warning("Hit max tool iterations, returning last response")

        # Get updated customer data from tool executor
        updated_data = tool_executor.get_merged_customer_data()
        column_data = tool_executor.get_column_data()

        return response.content, updated_data, column_data, tool_call_records


def create_engine() -> ConversationEngine:
    """Create a conversation engine with default configuration."""
    return ConversationEngine()
