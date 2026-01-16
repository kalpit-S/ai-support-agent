import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Tool definitions for the LLM (OpenAI function calling format)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "save_customer_info",
            "description": "Save information learned about the customer to their profile. Call this when the customer shares their name or other info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "Customer's first name"
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Type of issue: 'order', 'refund', 'inventory', 'shipping', 'payout', 'dispute', 'other'"
                    },
                    "order_number": {
                        "type": "string",
                        "description": "Order number being discussed (e.g., 'ORD-1001')"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Issue severity: 'low', 'medium', 'high', 'urgent'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up order details by order number. Use this when a customer asks about a specific order, wants to check status, or needs tracking info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number (e.g., 'ORD-1001')"
                    }
                },
                "required": ["order_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check stock levels for a product. Use this when a customer asks about inventory, stock availability, or product quantities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {
                        "type": "string",
                        "description": "Product SKU (e.g., 'SHIRT-BLU-XL')"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Product name to search for if SKU unknown"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund for an order. Use this when a customer requests a refund.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number to refund"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for refund: 'customer_request', 'item_not_received', 'item_damaged', 'wrong_item', 'courtesy'"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Partial refund amount (optional - if not provided, full refund is issued)"
                    }
                },
                "required": ["order_number", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_order_status",
            "description": "Update the status of an order. Use this to mark orders as shipped, add tracking, or cancel orders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status: 'processing', 'shipped', 'delivered', 'cancelled'"
                    },
                    "tracking_number": {
                        "type": "string",
                        "description": "Tracking number (required when marking as shipped)"
                    },
                    "carrier": {
                        "type": "string",
                        "description": "Shipping carrier: 'UPS', 'USPS', 'FedEx', 'DHL'"
                    }
                },
                "required": ["order_number", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_return_label",
            "description": "Generate a return shipping label for an order. Use this when processing a return.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number for the return"
                    }
                },
                "required": ["order_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search for help articles about policies, procedures, or how-to guides. Use for questions about shipping, returns, payments, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'return policy', 'shipping times', 'payout schedule')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: 'shipping', 'returns', 'orders', 'payments', 'inventory', 'disputes'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate to human support. Use for: fraud concerns, large refunds (>$500), angry customers, complex disputes, or explicit requests for human help.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority: 'normal', 'high', 'urgent'"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary for the human agent"
                    }
                },
                "required": ["reason"]
            }
        }
    }
]


class ToolExecutor:
    """Executes tools called by the LLM for Macrocenter e-commerce support."""

    def __init__(
        self,
        articles: List[Dict[str, Any]],
        orders: Optional[List[Dict[str, Any]]] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        inventory: Optional[List[Dict[str, Any]]] = None,
        customer_id: Optional[int] = None,
        existing_customer_data: Optional[Dict[str, Any]] = None,
    ):
        self.articles = articles
        self.orders = orders or []
        self.products = products or []
        self.inventory = inventory or []
        self.customer_id = customer_id
        self.existing_customer_data = existing_customer_data or {}

        # Index data for quick lookup
        self.articles_by_id = {a.get("article_id"): a for a in articles}
        self.orders_by_number = {o.get("order_number"): o for o in self.orders}
        self.products_by_sku = {p.get("sku"): p for p in self.products}
        self.inventory_by_product_id = {i.get("product_id"): i for i in self.inventory}

        # Track data to save
        self.saved_customer_data: Dict[str, Any] = {}
        self.saved_column_data: Dict[str, Any] = {}

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        handlers = {
            "save_customer_info": self._save_customer_info,
            "lookup_order": self._lookup_order,
            "check_inventory": self._check_inventory,
            "process_refund": self._process_refund,
            "update_order_status": self._update_order_status,
            "create_return_label": self._create_return_label,
            "search_knowledge_base": self._search_knowledge_base,
            "escalate_to_human": self._escalate_to_human,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = handler(arguments)
            logger.info(f"Tool {tool_name} result: {result}")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def _save_customer_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Save customer information to their profile."""
        saved_fields = []

        # Column fields
        if args.get("first_name"):
            self.saved_column_data["first_name"] = args["first_name"]
            saved_fields.append(f"name: {args['first_name']}")

        if args.get("company_name"):
            self.saved_column_data["company_name"] = args["company_name"]
            saved_fields.append(f"store: {args['company_name']}")

        # JSONB fields
        if args.get("issue_type"):
            self.saved_customer_data["issue_type"] = args["issue_type"]
            saved_fields.append(f"issue: {args['issue_type']}")

        if args.get("order_number"):
            self.saved_customer_data["order_number"] = args["order_number"]
            saved_fields.append(f"order: {args['order_number']}")

        if args.get("severity"):
            self.saved_customer_data["severity"] = args["severity"]
            saved_fields.append(f"severity: {args['severity']}")

        logger.info(f"Saved customer info: {saved_fields}")

        return {
            "success": True,
            "saved": saved_fields,
            "message": f"Saved: {', '.join(saved_fields)}" if saved_fields else "No new information to save"
        }

    def get_merged_customer_data(self) -> Dict[str, Any]:
        """Get the merged customer JSONB data."""
        merged = dict(self.existing_customer_data)
        merged.update(self.saved_customer_data)
        return merged

    def get_column_data(self) -> Dict[str, Any]:
        """Get data for dedicated database columns."""
        return dict(self.saved_column_data)

    def _lookup_order(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Look up order details by order number."""
        order_number = args.get("order_number", "").upper()

        # Normalize order number format
        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.orders_by_number.get(order_number)
        if not order:
            return {
                "error": f"Order {order_number} not found",
                "suggestion": "Please verify the order number and try again."
            }

        # Get order items
        items = order.get("items", [])
        items_summary = [
            {
                "sku": item.get("sku"),
                "name": item.get("product_name"),
                "quantity": item.get("quantity"),
                "unit_price": float(item.get("unit_price", 0))
            }
            for item in items
        ]

        # Format shipping address
        address = order.get("shipping_address", {})
        address_str = ""
        if address:
            address_str = f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('zip', '')}"

        return {
            "order_number": order_number,
            "status": order.get("status"),
            "total": float(order.get("total", 0)),
            "items": items_summary,
            "item_count": len(items),
            "customer_name": order.get("customer_name"),
            "customer_email": order.get("customer_email"),
            "shipping_address": address_str,
            "tracking_number": order.get("tracking_number"),
            "carrier": order.get("carrier"),
            "notes": order.get("notes"),
            "created_at": str(order.get("created_at", "")),
            "message": f"Order {order_number}: {order.get('status')} - ${order.get('total')}"
        }

    def _check_inventory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check inventory levels for a product."""
        sku = args.get("sku", "").upper()
        product_name = args.get("product_name", "").lower()

        # Find product by SKU or name
        product = None
        if sku:
            product = self.products_by_sku.get(sku)

        if not product and product_name:
            # Search by name
            for p in self.products:
                if product_name in p.get("name", "").lower():
                    product = p
                    break

        if not product:
            return {
                "error": f"Product not found: {sku or product_name}",
                "suggestion": "Try searching with a different SKU or product name."
            }

        # Get inventory for this product
        inv = self.inventory_by_product_id.get(product.get("id"))
        quantity = inv.get("quantity", 0) if inv else 0
        threshold = inv.get("low_stock_threshold", 5) if inv else 5

        # Determine stock status
        if quantity == 0:
            stock_status = "out_of_stock"
        elif quantity <= threshold:
            stock_status = "low_stock"
        else:
            stock_status = "in_stock"

        return {
            "sku": product.get("sku"),
            "name": product.get("name"),
            "price": float(product.get("price", 0)),
            "category": product.get("category"),
            "quantity": quantity,
            "warehouse": inv.get("warehouse", "main") if inv else "main",
            "low_stock_threshold": threshold,
            "stock_status": stock_status,
            "message": f"{product.get('name')}: {quantity} in stock ({stock_status})"
        }

    def _process_refund(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund for an order."""
        order_number = args.get("order_number", "").upper()
        reason = args.get("reason", "customer_request")
        partial_amount = args.get("amount")

        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.orders_by_number.get(order_number)
        if not order:
            return {"error": f"Order {order_number} not found"}

        # Check if already refunded
        if order.get("status") == "refunded":
            return {
                "error": f"Order {order_number} has already been refunded",
                "status": "refunded"
            }

        # Calculate refund amount
        order_total = float(order.get("total", 0))
        refund_amount = partial_amount if partial_amount else order_total

        # Check for large refund (would need HITL in production)
        needs_approval = refund_amount > 500

        if needs_approval:
            return {
                "success": False,
                "needs_approval": True,
                "order_number": order_number,
                "refund_amount": refund_amount,
                "reason": reason,
                "message": f"Refund of ${refund_amount:.2f} requires manager approval (over $500). Escalating to support team."
            }

        return {
            "success": True,
            "order_number": order_number,
            "refund_amount": refund_amount,
            "original_total": order_total,
            "refund_type": "partial" if partial_amount else "full",
            "reason": reason,
            "customer_email": order.get("customer_email"),
            "message": f"Refund of ${refund_amount:.2f} initiated for {order_number}. Customer will see it in 3-5 business days."
        }

    def _update_order_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update order status."""
        order_number = args.get("order_number", "").upper()
        new_status = args.get("status", "").lower()
        tracking = args.get("tracking_number")
        carrier = args.get("carrier")

        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.orders_by_number.get(order_number)
        if not order:
            return {"error": f"Order {order_number} not found"}

        valid_statuses = ["processing", "shipped", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            return {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}

        # Validate shipping info if marking as shipped
        if new_status == "shipped" and not tracking:
            return {
                "error": "Tracking number required when marking order as shipped",
                "suggestion": "Please provide a tracking number."
            }

        current_status = order.get("status")

        return {
            "success": True,
            "order_number": order_number,
            "previous_status": current_status,
            "new_status": new_status,
            "tracking_number": tracking,
            "carrier": carrier,
            "message": f"Order {order_number} updated: {current_status} → {new_status}" + (f" (tracking: {tracking})" if tracking else "")
        }

    def _create_return_label(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a return shipping label."""
        order_number = args.get("order_number", "").upper()

        if not order_number.startswith("ORD-"):
            order_number = f"ORD-{order_number}"

        order = self.orders_by_number.get(order_number)
        if not order:
            return {"error": f"Order {order_number} not found"}

        # Generate mock return label
        label_id = f"RTN-{order_number.replace('ORD-', '')}-{datetime.now().strftime('%H%M')}"

        return {
            "success": True,
            "order_number": order_number,
            "return_label_id": label_id,
            "carrier": "USPS",
            "return_address": "Macrocenter Returns, 123 Warehouse Way, Austin TX 78701",
            "valid_until": "30 days from today",
            "message": f"Return label {label_id} created. Customer can print it from their order confirmation email or use this ID at any {order.get('carrier', 'USPS')} location."
        }

    def _search_knowledge_base(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for articles matching the query."""
        query = args.get("query", "").lower()
        category = args.get("category", "").lower()

        matches = []

        for article in self.articles:
            if article.get("status") != "published":
                continue

            metadata = article.get("metadata", {})

            # Check category match if specified
            if category and metadata.get("category", "").lower() != category:
                continue

            # Search in title, content, and tags
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            tags = [t.lower() for t in metadata.get("tags", [])]

            # Keyword matching
            query_words = query.split()
            score = 0
            for word in query_words:
                if word in title:
                    score += 3
                if word in content:
                    score += 1
                if any(word in tag for tag in tags):
                    score += 2

            if score > 0:
                matches.append({
                    "article_id": article.get("article_id"),
                    "title": article.get("title"),
                    "category": metadata.get("category"),
                    "summary": content[:150] + "..." if len(content) > 150 else content,
                    "score": score
                })

        matches.sort(key=lambda x: x["score"], reverse=True)

        return {
            "found": len(matches),
            "articles": matches[:5],
            "message": f"Found {len(matches)} relevant article(s)" if matches else "No matching articles found"
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
            "reason": reason,
            "expected_response": response_times.get(priority, "within 24 hours"),
            "message": f"Escalated to support team. Ticket: {ticket_number}. A human agent will respond {response_times.get(priority, 'within 24 hours')}."
        }
