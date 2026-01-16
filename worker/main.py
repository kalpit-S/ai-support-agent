# worker/main.py
# Background worker that processes batched customer messages.
# Uses shared models to ensure consistency with API.

import logging
import time
from datetime import datetime

from config import settings
from batcher import create_batcher, Batch

# Import from shared module - single source of truth for models
from shared.database import get_engine, get_session_factory
from shared.models import (
    Customer,
    Message,
    KnowledgeBaseArticle,
    Product,
    Inventory,
    Order,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create database connection using shared utilities
engine = get_engine(settings.database_url)
SessionLocal = get_session_factory(engine)


def process_batch(batch: Batch) -> None:
    """Process a batch of messages using the LLM agent."""
    logger.info(f"Processing batch {batch.batch_id}")
    logger.info(f"  Customer ID: {batch.customer_id}")
    logger.info(f"  Message IDs: {batch.message_ids}")

    db = SessionLocal()

    try:
        # Load customer data
        customer = db.query(Customer).filter(Customer.id == batch.customer_id).first()

        if not customer:
            logger.error(f"Customer not found for ID {batch.customer_id}")
            return

        logger.info(f"  Customer: {customer.phone_number or customer.email}")
        logger.info(f"  Extracted data: {customer.extracted_data}")

        # Load messages in this batch
        messages = db.query(Message).filter(
            Message.id.in_(batch.message_ids)
        ).order_by(Message.created_at).all()

        logger.info(f"  Messages in batch:")
        for msg in messages:
            logger.info(f"    [{msg.direction}] {msg.content}")

        # Load full conversation history
        all_messages = db.query(Message).filter(
            Message.customer_id == customer.id
        ).order_by(Message.created_at).all()

        logger.info(f"  Total messages in conversation: {len(all_messages)}")

        # Load knowledge base articles
        articles = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.status == "published"
        ).all()
        logger.info(f"  Available KB articles: {len(articles)}")

        # Load products, inventory, and orders for e-commerce tools
        # NOTE: For this demo, we load all data into memory since the dataset is small.
        # In production, you'd pass the DB session to ToolExecutor and query inside
        # each tool (e.g., SELECT * FROM orders WHERE order_number = ?).
        products = db.query(Product).all()
        inventory = db.query(Inventory).all()
        orders = db.query(Order).all()
        logger.info(f"  Available products: {len(products)}, orders: {len(orders)}")

        # Prepare data for the conversation engine
        messages_data = [
            {"direction": m.direction, "content": m.content, "channel": m.channel}
            for m in all_messages
        ]
        articles_data = [
            {
                "id": a.id,
                "article_id": a.article_id,
                "title": a.title,
                "content": a.content,
                "status": a.status,
                "metadata": a.article_metadata or {},
            }
            for a in articles
        ]
        products_data = [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "description": p.description,
                "price": str(p.price),  # Convert Decimal to string for JSON
                "category": p.category,
            }
            for p in products
        ]
        inventory_data = [
            {
                "id": i.id,
                "product_id": i.product_id,
                "quantity": i.quantity,
                "warehouse": i.warehouse,
                "low_stock_threshold": i.low_stock_threshold,
            }
            for i in inventory
        ]
        orders_data = [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_id": o.customer_id,
                "status": o.status,
                "total": str(o.total),  # Convert Decimal to string for JSON
                "shipping_address": o.shipping_address,
                "tracking_number": o.tracking_number,
                "carrier": o.carrier,
                "customer_name": o.customer_name,
                "customer_email": o.customer_email,
                "notes": o.notes,
                "created_at": o.created_at,
                "items": [
                    {
                        "sku": item.sku,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),  # Convert Decimal to string
                    }
                    for item in o.items
                ]
            }
            for o in orders
        ]

        # Run the conversation engine
        from conversation.engine import create_engine
        conv_engine = create_engine()
        result = conv_engine.process_turn(
            customer_data=customer.extracted_data or {},
            messages=messages_data,
            articles=articles_data,
            customer_id=customer.id,
            orders=orders_data,
            products=products_data,
            inventory=inventory_data,
        )

        # Update customer extracted_data if changed
        if result.extracted_data:
            customer.extracted_data = result.extracted_data
            logger.info(f"  Updated customer extracted_data: {customer.extracted_data}")

        # Update column data if changed
        if result.column_data:
            if "first_name" in result.column_data:
                customer.first_name = result.column_data["first_name"]
                logger.info(f"  Updated customer first_name: {customer.first_name}")
            if "company_name" in result.column_data:
                customer.company_name = result.column_data["company_name"]
                logger.info(f"  Updated customer company_name: {customer.company_name}")
            if "account_tier" in result.column_data:
                customer.account_tier = result.column_data["account_tier"]
                logger.info(f"  Updated customer account_tier: {customer.account_tier}")
            if "email" in result.column_data and result.column_data["email"]:
                customer.email = result.column_data["email"]
                logger.info(f"  Updated customer email: {customer.email}")
            if "phone" in result.column_data and result.column_data["phone"]:
                customer.phone_number = result.column_data["phone"]
                logger.info(f"  Updated customer phone_number: {customer.phone_number}")

        # Get response text and determine output channel
        response_text = result.response_text

        # Check if agent specified a channel with [EMAIL] or [SMS] prefix
        outbound_channel = None
        if response_text.startswith("[EMAIL]"):
            outbound_channel = "email"
            response_text = response_text[7:].lstrip()
            logger.info("  Agent chose to respond via EMAIL")
        elif response_text.startswith("[SMS]"):
            outbound_channel = "sms"
            response_text = response_text[5:].lstrip()
            logger.info("  Agent chose to respond via SMS")

        # Default: same channel as last inbound message
        if not outbound_channel:
            last_inbound = [m for m in messages if m.direction == "inbound"]
            outbound_channel = last_inbound[-1].channel if last_inbound else "sms"

        # Build metadata with tool calls
        metadata = {}
        if result.tool_calls:
            metadata["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "args": tc.args,
                    "result": tc.result,
                }
                for tc in result.tool_calls
            ]
            logger.info(f"  Tool calls to save: {[tc.name for tc in result.tool_calls]}")

        # Create outbound message
        outbound = Message(
            customer_id=customer.id,
            direction="outbound",
            channel=outbound_channel,
            content=response_text,
            batch_id=None,
            message_metadata=metadata,
            created_at=datetime.utcnow(),
        )
        db.add(outbound)
        db.commit()

        logger.info(f"  Created outbound message [{outbound_channel.upper()}]: {response_text}")
        logger.info(f"  Batch {batch.batch_id} processed successfully")

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def main():
    """Main entry point for the worker."""
    logger.info("=" * 60)
    logger.info("Worker starting")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Redis: {settings.redis_url}")
    logger.info(f"Batch window: {settings.batch_window_seconds}s")
    logger.info(f"Poll interval: {settings.poll_interval_seconds}s")
    logger.info("=" * 60)

    logger.info("Waiting 5s for services to be ready...")
    time.sleep(5)

    batcher = create_batcher()
    batcher.run(process_batch)


if __name__ == "__main__":
    main()
