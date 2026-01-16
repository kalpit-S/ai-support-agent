"""
Voice-specific tools for the support agent.
These are the same 8 tools as the worker, but self-contained for the API service.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Tool definitions for Gemini (simplified format - Gemini accepts Python functions directly)
def get_tool_definitions():
    """Return tool definitions for Gemini function calling."""
    return [
        lookup_order,
        check_inventory,
        process_refund,
        create_return_label,
        search_knowledge_base,
        escalate_to_human,
        send_followup,
    ]


def send_followup(channel: str, message: str) -> dict:
    """
    Send a follow-up message to the customer on a different channel (email or SMS).
    Use this when the customer needs written confirmation or detailed info they can reference later.

    Args:
        channel: Channel to send on ('email' or 'sms')
        message: The message content to send
    """
    pass


# --- Tool Functions (Gemini can call these directly) ---

def lookup_order(order_number: str) -> dict:
    """
    Look up order details by order number.
    Use this when a customer asks about a specific order, wants to check status, or needs tracking info.

    Args:
        order_number: The order number (e.g., 'ORD-1001' or just '1001')
    """
    # This will be implemented via ToolExecutor with DB access
    pass


def check_inventory(sku: str = "", product_name: str = "") -> dict:
    """
    Check stock levels for a product.
    Use this when a customer asks about inventory, stock availability, or product quantities.

    Args:
        sku: Product SKU (e.g., 'GPU-RTX4090')
        product_name: Product name to search for if SKU unknown
    """
    pass


def process_refund(order_number: str, reason: str, amount: float = None) -> dict:
    """
    Process a refund for an order. Use this when a customer requests a refund.

    Args:
        order_number: The order number to refund
        reason: Reason for refund (customer_request, item_not_received, item_damaged, wrong_item, courtesy)
        amount: Partial refund amount (optional - if not provided, full refund is issued)
    """
    pass


def create_return_label(order_number: str) -> dict:
    """
    Generate a return shipping label for an order. Use this when processing a return.

    Args:
        order_number: The order number for the return
    """
    pass


def search_knowledge_base(query: str, category: str = "") -> dict:
    """
    Search for help articles about policies, procedures, or how-to guides.
    Use for questions about shipping, returns, payments, compatibility, etc.

    Args:
        query: Search query (e.g., 'return policy', 'PSU requirements', 'CPU compatibility')
        category: Optional category filter (shipping, returns, orders, compatibility)
    """
    pass


def escalate_to_human(reason: str, priority: str = "normal", summary: str = "") -> dict:
    """
    Escalate to human support.
    Use for: fraud concerns, large refunds (>$500), angry customers, complex disputes.

    Args:
        reason: Reason for escalation
        priority: Priority level (normal, high, urgent)
        summary: Brief summary for the human agent
    """
    pass


class VoiceToolExecutor:
    """
    Executes tools for voice conversations.
    Uses direct DB queries instead of pre-loaded data for better scalability.
    """

    def __init__(self, db: Session, customer_id: Optional[int] = None):
        self.db = db
        self.customer_id = customer_id
        self.saved_customer_data: Dict[str, Any] = {}

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        logger.info(f"[Voice] Executing tool: {tool_name} with args: {arguments}")

        handlers = {
            "lookup_order": self._lookup_order,
            "check_inventory": self._check_inventory,
            "process_refund": self._process_refund,
            "create_return_label": self._create_return_label,
            "search_knowledge_base": self._search_knowledge_base,
            "escalate_to_human": self._escalate_to_human,
            "send_followup": self._send_followup,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = handler(arguments)
            logger.info(f"[Voice] Tool {tool_name} result: {result}")
            return result
        except Exception as e:
            logger.error(f"[Voice] Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def _lookup_order(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Look up order by order number - queries DB directly."""
        from models import Order, OrderItem

        order_number = args.get("order_number", "").upper()
        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.db.query(Order).filter(Order.order_number == order_number).first()
        if not order:
            return {
                "error": f"Order {order_number} not found",
                "suggestion": "Please verify the order number and try again."
            }

        items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        items_summary = [
            {
                "sku": item.sku,
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0
            }
            for item in items
        ]

        address = order.shipping_address or {}
        address_str = ""
        if address:
            address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"

        return {
            "order_number": order_number,
            "status": order.status,
            "total": float(order.total) if order.total else 0,
            "items": items_summary,
            "item_count": len(items),
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "shipping_address": address_str,
            "tracking_number": order.tracking_number,
            "carrier": order.carrier,
            "message": f"Order {order_number}: {order.status} - ${order.total}"
        }

    def _check_inventory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check inventory - queries DB directly."""
        from models import Product, Inventory

        sku = args.get("sku", "").upper()
        product_name = args.get("product_name", "").lower()

        product = None
        if sku:
            product = self.db.query(Product).filter(Product.sku == sku).first()

        if not product and product_name:
            product = self.db.query(Product).filter(
                Product.name.ilike(f"%{product_name}%")
            ).first()

        if not product:
            return {
                "error": f"Product not found: {sku or product_name}",
                "suggestion": "Try searching with a different SKU or product name."
            }

        inv = self.db.query(Inventory).filter(Inventory.product_id == product.id).first()
        quantity = inv.quantity if inv else 0
        threshold = inv.low_stock_threshold if inv else 5

        if quantity == 0:
            stock_status = "out_of_stock"
        elif quantity <= threshold:
            stock_status = "low_stock"
        else:
            stock_status = "in_stock"

        return {
            "sku": product.sku,
            "name": product.name,
            "price": float(product.price) if product.price else 0,
            "category": product.category,
            "quantity": quantity,
            "stock_status": stock_status,
            "message": f"{product.name}: {quantity} in stock ({stock_status})"
        }

    def _process_refund(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund."""
        from models import Order

        order_number = args.get("order_number", "").upper()
        reason = args.get("reason", "customer_request")
        partial_amount = args.get("amount")

        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.db.query(Order).filter(Order.order_number == order_number).first()
        if not order:
            return {"error": f"Order {order_number} not found"}

        if order.status == "refunded":
            return {"error": f"Order {order_number} has already been refunded"}

        order_total = float(order.total) if order.total else 0
        refund_amount = partial_amount if partial_amount else order_total

        # HITL: Large refunds need approval
        if refund_amount > 500:
            return {
                "success": False,
                "needs_approval": True,
                "order_number": order_number,
                "refund_amount": refund_amount,
                "message": f"Refund of ${refund_amount:.2f} requires manager approval (over $500). I'll escalate this for you."
            }

        return {
            "success": True,
            "order_number": order_number,
            "refund_amount": refund_amount,
            "refund_type": "partial" if partial_amount else "full",
            "reason": reason,
            "message": f"Refund of ${refund_amount:.2f} initiated for {order_number}. You'll see it in 3-5 business days."
        }

    def _create_return_label(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a return shipping label."""
        from models import Order

        order_number = args.get("order_number", "").upper()
        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.db.query(Order).filter(Order.order_number == order_number).first()
        if not order:
            return {"error": f"Order {order_number} not found"}

        label_id = f"RTN-{order_number.replace('ORD-', '')}-{datetime.now().strftime('%H%M')}"

        return {
            "success": True,
            "order_number": order_number,
            "return_label_id": label_id,
            "carrier": "USPS",
            "return_address": "Macrocenter Returns, 123 Warehouse Way, Austin TX 78701",
            "message": f"Return label {label_id} created. I'll email it to you shortly."
        }

    def _search_knowledge_base(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base articles."""
        from models import KnowledgeBaseArticle

        query = args.get("query", "").lower()
        category = args.get("category", "").lower()

        # Query articles
        articles_query = self.db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.status == "published"
        )

        articles = articles_query.all()
        matches = []

        for article in articles:
            metadata = article.article_metadata or {}

            if category and metadata.get("category", "").lower() != category:
                continue

            title = (article.title or "").lower()
            content = (article.content or "").lower()
            tags = [t.lower() for t in metadata.get("tags", [])]

            score = 0
            for word in query.split():
                if word in title:
                    score += 3
                if word in content:
                    score += 1
                if any(word in tag for tag in tags):
                    score += 2

            if score > 0:
                matches.append({
                    "article_id": article.article_id,
                    "title": article.title,
                    "category": metadata.get("category"),
                    "summary": content[:200] + "..." if len(content) > 200 else content,
                    "score": score
                })

        matches.sort(key=lambda x: x["score"], reverse=True)

        if matches:
            top = matches[0]
            return {
                "found": len(matches),
                "top_result": top,
                "message": f"Found {len(matches)} article(s). Top match: {top['title']}"
            }
        return {
            "found": 0,
            "message": "No matching articles found. Let me help you directly."
        }

    def _escalate_to_human(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate to human support."""
        reason = args.get("reason", "Unspecified")
        priority = args.get("priority", "normal")
        summary = args.get("summary", "")

        response_times = {
            "normal": "within 24 hours",
            "high": "within 4 hours",
            "urgent": "within 1 hour"
        }

        ticket_number = f"TKT-{self.customer_id or 'NEW'}-{datetime.now().strftime('%Y%m%d%H%M')}"

        return {
            "success": True,
            "ticket_number": ticket_number,
            "priority": priority,
            "expected_response": response_times.get(priority, "within 24 hours"),
            "message": f"I've escalated this to our support team. Ticket {ticket_number} - someone will reach out {response_times.get(priority, 'soon')}."
        }

    def _send_followup(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send a follow-up message on email or SMS."""
        from models import Message

        channel = args.get("channel", "email").lower()
        content = args.get("message", "")

        if channel not in ("email", "sms"):
            return {"error": f"Invalid channel: {channel}. Use 'email' or 'sms'."}

        if not content:
            return {"error": "Message content is required."}

        if not self.customer_id:
            return {"error": "No customer associated with this session."}

        # Create the message in the database
        message = Message(
            customer_id=self.customer_id,
            direction="outbound",
            channel=channel,
            content=content,
            batch_id=None,
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        self.db.commit()

        logger.info(f"[Voice] Sent follow-up via {channel.upper()}: {content[:50]}...")

        return {
            "success": True,
            "channel": channel,
            "message": f"Follow-up sent via {channel.upper()}."
        }
