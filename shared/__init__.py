# Shared models and database utilities for API and Worker
from shared.database import Base, get_engine, get_session_factory
from shared.models import (
    Customer,
    Message,
    KnowledgeBaseArticle,
    Ticket,
    Product,
    Inventory,
    Order,
    OrderItem,
)

__all__ = [
    "Base",
    "get_engine",
    "get_session_factory",
    "Customer",
    "Message",
    "KnowledgeBaseArticle",
    "Ticket",
    "Product",
    "Inventory",
    "Order",
    "OrderItem",
]
