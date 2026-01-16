"""Tests for the FastAPI application."""

import pytest
import requests
import redis
import time


API_BASE_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379/0"


def test_health_endpoint():
    """Verify /health returns healthy status."""
    response = requests.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    """Verify / returns API info JSON."""
    response = requests.get(f"{API_BASE_URL}/")
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")
    data = response.json()
    assert "name" in data
    assert "Macrocenter" in data["name"]


def test_list_articles():
    """Verify /articles returns the seeded knowledge base articles."""
    response = requests.get(f"{API_BASE_URL}/articles")
    assert response.status_code == 200
    articles = response.json()

    # Should have at least the 6 seeded articles
    assert len(articles) >= 6

    article = articles[0]
    assert "id" in article
    assert "article_id" in article
    assert "title" in article
    assert "content" in article


def test_get_specific_article():
    """Verify /articles/{id} returns a specific article."""
    response = requests.get(f"{API_BASE_URL}/articles/1")
    assert response.status_code == 200
    article = response.json()
    assert article["article_id"] == "KB001"
    # First article is CPU & Motherboard Compatibility Guide
    assert "cpu" in article["title"].lower() or "compatibility" in article["title"].lower()


def test_get_nonexistent_article():
    """Verify /articles/{id} returns 404 for unknown article."""
    response = requests.get(f"{API_BASE_URL}/articles/9999")
    assert response.status_code == 404


def test_list_customers():
    """Verify /customers returns a list."""
    response = requests.get(f"{API_BASE_URL}/customers")
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)


def test_webhook_creates_customer():
    """Verify webhook creates a new customer."""
    phone = "+15550001111"

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Test message from pytest"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "received"
    assert "message_id" in data
    assert "customer_id" in data
    assert "batch_id" in data

    customer_id = data["customer_id"]
    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    assert customer_response.status_code == 200
    customer = customer_response.json()
    assert customer["phone_number"] == phone


def test_webhook_stores_message():
    """Verify webhook stores the message."""
    phone = "+15550002222"
    message_text = "Hello, I need help with my order"

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": message_text}
    )

    assert response.status_code == 200
    data = response.json()
    customer_id = data["customer_id"]

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    customer = customer_response.json()

    messages = customer["messages"]
    assert len(messages) >= 1

    found = any(m["content"] == message_text for m in messages)
    assert found, f"Message '{message_text}' not found in customer messages"


def test_webhook_same_customer_same_phone():
    """Verify multiple messages from same phone go to same customer."""
    phone = "+15550003333"

    response1 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "First message"}
    )
    customer_id_1 = response1.json()["customer_id"]

    time.sleep(0.5)

    response2 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Second message"}
    )
    customer_id_2 = response2.json()["customer_id"]

    assert customer_id_1 == customer_id_2


def test_webhook_creates_redis_batch():
    """Verify webhook creates batch keys in Redis."""
    phone = "+15550004444"
    r = redis.from_url(REDIS_URL, decode_responses=True)

    response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Testing Redis batch"}
    )

    assert response.status_code == 200
    result = response.json()
    batch_id = result["batch_id"]
    customer_id = result["customer_id"]

    batch_key = f"batch:customer:{customer_id}"
    batch_id_key = f"{batch_key}:id"

    assert r.exists(batch_key), "Batch key should exist in Redis"
    assert r.exists(batch_id_key), "Batch ID key should exist in Redis"

    stored_batch_id = r.get(batch_id_key)
    assert stored_batch_id == batch_id


def test_webhook_batch_accumulates_messages():
    """Verify rapid messages share the same batch_id."""
    phone = "+15550005555"

    response1 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Message 1"}
    )
    batch_id_1 = response1.json()["batch_id"]

    response2 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Message 2"}
    )
    batch_id_2 = response2.json()["batch_id"]

    assert batch_id_1 == batch_id_2, "Rapid messages should share batch_id"


def test_email_webhook_creates_customer():
    """Verify email webhook creates a new customer."""
    email = "testcustomer@example.com"

    response = requests.post(
        f"{API_BASE_URL}/webhook/email",
        json={"from_email": email, "body": "Test message via email"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "received"
    assert "message_id" in data
    assert "customer_id" in data
    assert "batch_id" in data

    customer_id = data["customer_id"]
    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    assert customer_response.status_code == 200
    customer = customer_response.json()
    assert customer["email"] == email


def test_email_webhook_stores_message_with_channel():
    """Verify email webhook stores message with channel='email'."""
    email = "emailchannel@example.com"
    message_text = "Hello from email channel"

    response = requests.post(
        f"{API_BASE_URL}/webhook/email",
        json={"from_email": email, "body": message_text}
    )

    assert response.status_code == 200
    customer_id = response.json()["customer_id"]

    customer_response = requests.get(f"{API_BASE_URL}/customers/{customer_id}")
    customer = customer_response.json()
    messages = customer["messages"]

    our_msg = [m for m in messages if m["content"] == message_text]
    assert len(our_msg) >= 1, "Message not found"
    assert our_msg[0]["channel"] == "email", "Channel should be 'email'"


def test_same_customer_sms_and_email():
    """Verify SMS messages are unified for the same phone."""
    phone = "+15559998888"

    sms_response = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Initial SMS message"}
    )
    assert sms_response.status_code == 200
    sms_customer_id = sms_response.json()["customer_id"]

    sms_response2 = requests.post(
        f"{API_BASE_URL}/webhook/sms",
        json={"from_number": phone, "body": "Follow up SMS"}
    )
    assert sms_response2.json()["customer_id"] == sms_customer_id, "Same phone should be same customer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
