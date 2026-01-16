"""Tests that verify Docker infrastructure is working."""

import psycopg2
import redis
import pytest


def test_postgres_connection():
    """Verify Postgres connection."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="support_db",
        user="support",
        password="support_dev"
    )
    assert conn is not None
    conn.close()


def test_all_tables_exist():
    """Verify all tables were created by init.sql."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="support_db",
        user="support",
        password="support_dev"
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    tables = [row[0] for row in cursor.fetchall()]
    expected_tables = [
        'customers',
        'inventory',
        'knowledge_base',
        'messages',
        'order_items',
        'orders',
        'products',
        'tickets'
    ]
    assert tables == expected_tables, f"Expected {expected_tables}, got {tables}"

    cursor.close()
    conn.close()


def test_seed_data_loaded():
    """Verify seed.sql loaded the sample data."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="support_db",
        user="support",
        password="support_dev"
    )
    cursor = conn.cursor()

    # Check knowledge base articles
    cursor.execute("SELECT COUNT(*) FROM knowledge_base")
    article_count = cursor.fetchone()[0]
    assert article_count >= 6, f"Expected at least 6 KB articles, got {article_count}"

    # Check specific article (KB001 = CPU & Motherboard Compatibility)
    cursor.execute("SELECT article_id, title FROM knowledge_base WHERE article_id = 'KB001'")
    article = cursor.fetchone()
    assert article is not None, "KB001 article not found"
    assert "CPU" in article[1] or "Compatibility" in article[1], f"Article title should be about CPU compatibility, got: {article[1]}"

    # Check products loaded
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    assert product_count >= 30, f"Expected at least 30 products, got {product_count}"

    # Check orders loaded
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count = cursor.fetchone()[0]
    assert order_count >= 5, f"Expected at least 5 orders, got {order_count}"

    cursor.close()
    conn.close()


def test_jsonb_metadata_queryable():
    """Verify JSONB metadata field is queryable."""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="support_db",
        user="support",
        password="support_dev"
    )
    cursor = conn.cursor()

    # Query articles by category in metadata
    cursor.execute("""
        SELECT article_id
        FROM knowledge_base
        WHERE metadata->>'category' = 'compatibility'
    """)

    results = cursor.fetchall()
    assert len(results) >= 1, "Should find at least 1 article with category = 'compatibility'"
    article_ids = [r[0] for r in results]
    assert 'KB001' in article_ids, "KB001 should have category = 'compatibility'"

    cursor.close()
    conn.close()


def test_redis_connection():
    """Verify Redis connection."""
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    assert r.ping() is True, "Redis should respond to PING"


def test_redis_basic_operations():
    """Verify basic Redis operations work."""
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # Test key-value
    r.set('test_key', 'test_value')
    assert r.get('test_key') == 'test_value'

    # Test list operations (used for batching)
    r.delete('test_list')
    r.lpush('test_list', 'message1')
    r.lpush('test_list', 'message2')
    messages = r.lrange('test_list', 0, -1)
    assert len(messages) == 2

    # Cleanup
    r.delete('test_key')
    r.delete('test_list')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
