# api/models.py
# Re-exports models from shared module.
# This ensures API and Worker use the exact same model definitions.

from shared.models import (
    Customer,
    KnowledgeBaseArticle,
    Message,
    Ticket,
    Product,
    Inventory,
    Order,
    OrderItem,
)

__all__ = [
    "Customer",
    "KnowledgeBaseArticle",
    "Message",
    "Ticket",
    "Product",
    "Inventory",
    "Order",
    "OrderItem",
]
