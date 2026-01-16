"""Tests for the agent tool executor."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'worker'))

from conversation.tools import ToolExecutor, TOOL_DEFINITIONS


# Sample data for testing (matches PC parts store context)
SAMPLE_ARTICLES = [
    {
        "id": 1,
        "article_id": "KB001",
        "title": "CPU & Motherboard Compatibility Guide",
        "content": "Before purchasing, verify CPU and motherboard socket compatibility. Intel uses LGA 1700, AMD uses AM5...",
        "status": "published",
        "metadata": {"category": "compatibility", "tags": ["cpu", "motherboard", "compatibility"]},
    },
    {
        "id": 2,
        "article_id": "KB002",
        "title": "GPU Power Requirements & PSU Guide",
        "content": "RTX 4090 requires 850W minimum PSU. RTX 4080 requires 750W minimum...",
        "status": "published",
        "metadata": {"category": "compatibility", "tags": ["gpu", "psu", "power"]},
    },
    {
        "id": 3,
        "article_id": "KB003",
        "title": "Return Policy - PC Components",
        "content": "Returns accepted within 30 days. GPUs and CPUs must be unopened unless DOA...",
        "status": "published",
        "metadata": {"category": "returns", "tags": ["return", "refund", "policy"]},
    },
]

SAMPLE_ORDERS = [
    {
        "id": 1,
        "order_number": "ORD-1001",
        "customer_id": 1,
        "status": "delivered",
        "total": 1599.99,
        "items": [{"sku": "GPU-RTX4090", "name": "RTX 4090", "quantity": 1, "unit_price": 1599.99}],
        "tracking_number": "1Z999AA10123456784",
        "carrier": "UPS",
    },
    {
        "id": 2,
        "order_number": "ORD-1002",
        "customer_id": 1,
        "status": "processing",
        "total": 349.99,
        "items": [{"sku": "CPU-7800X3D", "name": "Ryzen 7 7800X3D", "quantity": 1, "unit_price": 349.99}],
        "tracking_number": None,
        "carrier": None,
    },
]

SAMPLE_PRODUCTS = [
    {"id": 1, "sku": "GPU-RTX4090", "name": "NVIDIA GeForce RTX 4090 24GB", "price": 1599.99, "category": "GPU"},
    {"id": 2, "sku": "GPU-RTX4080", "name": "NVIDIA GeForce RTX 4080 16GB", "price": 1199.99, "category": "GPU"},
    {"id": 3, "sku": "CPU-7800X3D", "name": "AMD Ryzen 7 7800X3D", "price": 349.99, "category": "CPU"},
]

SAMPLE_INVENTORY = [
    {"id": 1, "product_id": 1, "sku": "GPU-RTX4090", "quantity": 5, "low_stock_threshold": 3},
    {"id": 2, "product_id": 2, "sku": "GPU-RTX4080", "quantity": 0, "low_stock_threshold": 3},
    {"id": 3, "product_id": 3, "sku": "CPU-7800X3D", "quantity": 12, "low_stock_threshold": 5},
]


def test_tool_definitions_exist():
    """Verify tool definitions are properly structured."""
    assert len(TOOL_DEFINITIONS) >= 8, "Should have at least 8 tools"

    tool_names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "save_customer_info" in tool_names
    assert "lookup_order" in tool_names
    assert "check_inventory" in tool_names
    assert "process_refund" in tool_names
    assert "update_order_status" in tool_names
    assert "create_return_label" in tool_names
    assert "search_knowledge_base" in tool_names
    assert "escalate_to_human" in tool_names


def test_tool_definitions_have_descriptions():
    """Verify all tools have descriptions."""
    for tool in TOOL_DEFINITIONS:
        assert "description" in tool["function"], f"Tool {tool['function']['name']} missing description"
        assert len(tool["function"]["description"]) > 10, "Description should be meaningful"


# === lookup_order tests ===

def test_lookup_order_success():
    """Verify lookup_order finds order by number."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("lookup_order", {"order_number": "ORD-1001"})

    assert result["order_number"] == "ORD-1001"
    assert result["status"] == "delivered"
    assert result["total"] == 1599.99
    assert "tracking_number" in result


def test_lookup_order_not_found():
    """Verify lookup_order handles missing order."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("lookup_order", {"order_number": "ORD-9999"})

    assert "error" in result or "not found" in result.get("message", "").lower()


# === check_inventory tests ===

def test_check_inventory_by_sku():
    """Verify check_inventory finds product by SKU."""
    executor = ToolExecutor(
        SAMPLE_ARTICLES,
        products=SAMPLE_PRODUCTS,
        inventory=SAMPLE_INVENTORY,
        customer_id=1
    )

    result = executor.execute("check_inventory", {"sku": "GPU-RTX4090"})

    assert result["sku"] == "GPU-RTX4090"
    assert result["quantity"] == 5
    assert result["stock_status"] in ["in_stock", "low_stock", "out_of_stock"]


def test_check_inventory_out_of_stock():
    """Verify check_inventory reports out of stock."""
    executor = ToolExecutor(
        SAMPLE_ARTICLES,
        products=SAMPLE_PRODUCTS,
        inventory=SAMPLE_INVENTORY,
        customer_id=1
    )

    result = executor.execute("check_inventory", {"sku": "GPU-RTX4080"})

    assert result["quantity"] == 0
    assert result["stock_status"] == "out_of_stock"


def test_check_inventory_not_found():
    """Verify check_inventory handles unknown product."""
    executor = ToolExecutor(
        SAMPLE_ARTICLES,
        products=SAMPLE_PRODUCTS,
        inventory=SAMPLE_INVENTORY,
        customer_id=1
    )

    result = executor.execute("check_inventory", {"sku": "UNKNOWN-SKU"})

    assert "error" in result or "not found" in result.get("message", "").lower()


# === search_knowledge_base tests ===

def test_search_knowledge_base_finds_matches():
    """Verify search_knowledge_base finds matching articles."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("search_knowledge_base", {"query": "PSU power GPU"})

    assert result["found"] >= 1, "Should find at least 1 article"
    assert len(result["articles"]) >= 1
    article_ids = [a["article_id"] for a in result["articles"]]
    assert "KB002" in article_ids


def test_search_knowledge_base_by_category():
    """Verify search_knowledge_base filters by category."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    # Need both query and category - category filters, query scores
    result = executor.execute("search_knowledge_base", {"query": "return refund", "category": "returns"})

    assert result["found"] >= 1
    article_ids = [a["article_id"] for a in result["articles"]]
    assert "KB003" in article_ids


def test_search_knowledge_base_no_matches():
    """Verify search_knowledge_base when no articles match."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("search_knowledge_base", {"query": "nonexistent topic xyz"})

    assert result["found"] == 0
    assert len(result["articles"]) == 0


# === process_refund tests ===

def test_process_refund_success():
    """Verify process_refund for valid order."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("process_refund", {
        "order_number": "ORD-1001",
        "reason": "Customer requested"
    })

    # Small refunds should succeed, large ones escalate
    assert "success" in result or "requires_escalation" in result


def test_process_refund_order_not_found():
    """Verify process_refund for non-existent order."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("process_refund", {
        "order_number": "ORD-9999",
        "reason": "Customer requested"
    })

    assert result.get("success") == False or "error" in result


# === escalate_to_human tests ===

def test_escalate_to_human_success():
    """Verify escalate_to_human returns success with ticket details."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=123)

    result = executor.execute("escalate_to_human", {
        "reason": "Customer needs special assistance",
        "priority": "high",
    })

    assert result["success"] == True
    assert "ticket_number" in result
    assert "message" in result


def test_escalate_to_human_default_priority():
    """Verify escalate_to_human uses default priority."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("escalate_to_human", {
        "reason": "Complex issue",
    })

    assert result["success"] == True
    assert "ticket_number" in result


# === save_customer_info tests ===

def test_save_customer_info_basic():
    """Verify saving basic customer info."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("save_customer_info", {
        "first_name": "John",
        "issue_type": "refund",
    })

    assert result["success"] == True
    column_data = executor.get_column_data()
    assert column_data["first_name"] == "John"


def test_save_customer_info_merges_with_existing():
    """Verify new info merges with existing customer data."""
    existing_data = {"issue_type": "order"}
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1, existing_customer_data=existing_data)

    result = executor.execute("save_customer_info", {
        "issue_type": "refund",
        "order_number": "ORD-1001",
    })

    assert result["success"] == True
    merged = executor.get_merged_customer_data()
    assert merged["issue_type"] == "refund"  # New value overrides
    assert merged["order_number"] == "ORD-1001"


def test_save_customer_info_empty():
    """Verify saving empty info returns appropriate message."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("save_customer_info", {})

    assert result["success"] == True
    assert "No new information" in result["message"]


# === create_return_label tests ===

def test_create_return_label_success():
    """Verify create_return_label for valid order."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("create_return_label", {"order_number": "ORD-1001"})

    assert result["success"] == True
    assert "return_label_id" in result


def test_create_return_label_order_not_found():
    """Verify create_return_label for non-existent order."""
    executor = ToolExecutor(SAMPLE_ARTICLES, orders=SAMPLE_ORDERS, customer_id=1)

    result = executor.execute("create_return_label", {"order_number": "ORD-9999"})

    assert result.get("success") == False or "error" in result


# === unknown tool test ===

def test_unknown_tool():
    """Verify unknown tools return error."""
    executor = ToolExecutor(SAMPLE_ARTICLES, customer_id=1)

    result = executor.execute("unknown_tool", {})

    assert "error" in result
    assert "unknown" in result["error"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
