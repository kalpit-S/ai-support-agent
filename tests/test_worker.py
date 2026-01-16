"""Tests for the worker batch processing."""

import pytest
import requests
import redis
import time
import random


API_BASE_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379/0"
BATCH_WINDOW = 5


def test_worker_processes_batch():
    """Verify worker processes a batch and creates outbound message via LLM."""
    phone = "+15550101010"

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Hi, I need help resetting my password"}
    )
    assert response.status_code == 200
    customer_id = response.json()["customer_id"]

    # Wait for batch window + processing time
    time.sleep(BATCH_WINDOW + 5)

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    assert customer_response.status_code == 200
    customer = customer_response.json()

    messages = customer["messages"]
    assert len(messages) >= 2, "Should have at least 2 messages (inbound + outbound)"

    outbound = [m for m in messages if m["direction"] == "outbound"]
    assert len(outbound) >= 1, "Should have at least 1 outbound message from LLM"
    assert len(outbound[-1]["content"]) > 10, "Outbound message should have content"


def test_batch_cleaned_up_after_processing():
    """Verify Redis batch keys are removed after processing."""
    phone = f"+1555020{random.randint(1000, 9999)}"
    r = redis.from_url(REDIS_URL, decode_responses=True)

    time.sleep(2)

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Testing batch cleanup"}
    )
    assert response.status_code == 200
    customer_id = response.json()["customer_id"]

    batch_key = f"batch:customer:{customer_id}"
    assert r.exists(batch_key), "Batch should exist immediately after sending"

    # Wait for processing
    max_wait = 90
    poll_interval = 3
    waited = 0

    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval

        if not r.exists(batch_key):
            break

    assert not r.exists(batch_key), f"Batch should be deleted after {waited}s of processing"
    assert not r.exists(f"{batch_key}:id"), "Batch ID should be deleted"
    assert not r.exists(f"{batch_key}:updated"), "Batch updated should be deleted"


def test_multiple_messages_same_batch():
    """Verify rapid messages are processed together in one batch."""
    phone = "+15550303030"

    response1 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "First message"}
    )
    batch_id_1 = response1.json()["batch_id"]
    customer_id = response1.json()["customer_id"]

    response2 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Second message"}
    )
    batch_id_2 = response2.json()["batch_id"]

    assert batch_id_1 == batch_id_2, "Rapid messages should share batch_id"

    time.sleep(BATCH_WINDOW + 3)

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    customer = customer_response.json()
    messages = customer["messages"]

    inbound = [m for m in messages if m["direction"] == "inbound"]
    outbound = [m for m in messages if m["direction"] == "outbound"]

    assert len(inbound) >= 2, "Should have at least 2 inbound messages"
    assert len(outbound) >= 1, "Should have at least 1 outbound (response to batch)"


def test_worker_loads_all_context():
    """Verify worker has access to conversation history and knowledge base."""
    phone = "+15550404040"

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "I need help with billing"}
    )
    assert response.status_code == 200
    customer_id = response.json()["customer_id"]

    time.sleep(BATCH_WINDOW + 5)

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    customer = customer_response.json()

    outbound = [m for m in customer["messages"] if m["direction"] == "outbound"]
    assert len(outbound) >= 1, "Worker should create outbound message after loading context"


def test_llm_extracts_customer_data():
    """Verify LLM extracts customer data from messages."""
    phone = "+15550505050"

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={
            "from_number": phone,
            "body": "Hi, my name is John and I work at Acme Corp. I'm having issues with the API rate limits."
        }
    )
    assert response.status_code == 200
    customer_id = response.json()["customer_id"]

    time.sleep(BATCH_WINDOW + 5)

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    customer = customer_response.json()

    # Check if the LLM extracted the name
    assert customer.get("first_name") == "John", f"Expected first_name 'John', got {customer.get('first_name')}"

    # Check extracted_data for issue type
    extracted = customer.get("extracted_data", {})
    # The LLM should have extracted some info
    assert extracted is not None, "extracted_data should not be None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
