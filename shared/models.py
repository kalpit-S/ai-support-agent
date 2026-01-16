# shared/models.py
# SQLAlchemy models shared between API and Worker.
# This is the single source of truth for all database models.

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.database import Base


# ============================================================
# CUSTOMER SUPPORT MODELS
# ============================================================

class Customer(Base):
    """A customer in the system, identified by phone number or email."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="customer",
        order_by="Message.created_at",
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        back_populates="customer",
    )

    def __repr__(self):
        return f"<Customer {self.id}: {self.phone_number or self.email}>"


class KnowledgeBaseArticle(Base):
    """A help article in the knowledge base that the agent can reference."""
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Note: Column name is "metadata" but Python attr is "article_metadata"
    # because "metadata" is reserved in SQLAlchemy
    article_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeBaseArticle {self.article_id}: {self.title[:30]}...>"


class Message(Base):
    """A single message in a customer's conversation."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="sms", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    batch_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    # Note: Column name is "metadata" but Python attr is "message_metadata"
    # because "metadata" is reserved in SQLAlchemy
    message_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="messages")

    def __repr__(self):
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<Message {self.id} ({self.direction}): {preview}>"


class Ticket(Base):
    """Tracks a customer's support ticket for human escalation."""
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    article_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("knowledge_base.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    issue_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")
    article: Mapped[Optional["KnowledgeBaseArticle"]] = relationship("KnowledgeBaseArticle")

    def __repr__(self):
        return f"<Ticket {self.id} customer={self.customer_id} status={self.status}>"


# ============================================================
# E-COMMERCE MODELS
# ============================================================

class Product(Base):
    """A product in the Macrocenter catalog."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    inventory: Mapped[Optional["Inventory"]] = relationship("Inventory", back_populates="product", uselist=False)
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"


class Inventory(Base):
    """Stock levels for a product."""
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warehouse: Mapped[str] = mapped_column(String(100), default="main")
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="inventory")

    @property
    def stock_status(self) -> str:
        """Return stock status based on quantity and threshold."""
        if self.quantity == 0:
            return "out_of_stock"
        elif self.quantity <= self.low_stock_threshold:
            return "low_stock"
        return "in_stock"

    def __repr__(self):
        return f"<Inventory product_id={self.product_id} qty={self.quantity}>"


class Order(Base):
    """A customer order in Macrocenter."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("customers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order")

    def __repr__(self):
        return f"<Order {self.order_number} status={self.status} total=${self.total}>"


class OrderItem(Base):
    """A line item in an order."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="order_items")

    @property
    def line_total(self) -> Decimal:
        """Calculate total for this line item."""
        return self.quantity * self.unit_price

    def __repr__(self):
        return f"<OrderItem {self.sku} x{self.quantity} @ ${self.unit_price}>"
