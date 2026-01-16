-- init.sql
-- This file runs once when the Postgres container first starts.
-- It creates all our tables. If you need to re-run it, you must:
--   docker-compose down -v   (the -v deletes the data volume)
--   docker-compose up        (starts fresh)

-- ============================================================
-- CUSTOMERS TABLE
-- ============================================================
-- One row per customer. Identified by phone number (SMS) or email.
-- Multi-channel: a customer may have phone, email, or both.
-- extracted_data is JSONB - flexible storage for whatever info we collect
-- (issue_type, product, account_tier, etc.) without needing to add columns.
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,

    -- Phone number is how we identify incoming SMS
    -- UNIQUE constraint means no duplicates allowed
    -- Nullable because email-only customers may not have a phone
    phone_number VARCHAR(20) UNIQUE,

    -- Email is how we identify incoming emails
    -- UNIQUE constraint for lookup by email address
    email VARCHAR(255) UNIQUE,

    -- Basic info (nullable - we collect these over time)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(200),
    account_tier VARCHAR(50),  -- e.g., 'free', 'pro', 'enterprise'

    -- JSONB column for flexible data storage
    -- Example: {"issue_type": "billing", "product": "api", "severity": "high"}
    -- JSONB is binary JSON - faster to query than regular JSON, can be indexed
    extracted_data JSONB DEFAULT '{}',

    -- Timestamps for debugging and auditing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on phone_number for fast lookups when SMS arrives
CREATE INDEX idx_customers_phone ON customers(phone_number);

-- Index on email for fast lookups when email arrives
CREATE INDEX idx_customers_email ON customers(email);

-- ============================================================
-- KNOWLEDGE_BASE TABLE
-- ============================================================
-- Help articles and documentation that the agent can search.
-- The agent uses these to answer customer questions.
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,

    -- Unique article identifier (e.g., "KB001", "billing-faq")
    article_id VARCHAR(50) UNIQUE NOT NULL,

    -- Human-readable info
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,  -- The actual help content

    -- Metadata for routing and filtering
    -- Example: {
    --   "category": "billing",
    --   "tags": ["payments", "invoices", "refunds"],
    --   "products": ["api", "dashboard"],
    --   "account_tiers": ["pro", "enterprise"]
    -- }
    metadata JSONB NOT NULL,

    -- Is this article currently published?
    status VARCHAR(50) DEFAULT 'published',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- MESSAGES TABLE
-- ============================================================
-- Every message in every conversation.
-- References customer directly (no separate conversations table needed
-- because each customer has exactly one conversation thread).
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,

    -- Which customer this message belongs to
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- 'inbound' = customer sent this, 'outbound' = we sent this
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),

    -- Which channel: 'sms' or 'email'
    -- LLM uses this to adapt response tone (formal for email, casual for SMS)
    channel VARCHAR(20) NOT NULL DEFAULT 'sms' CHECK (channel IN ('sms', 'email')),

    -- The actual message text
    content TEXT NOT NULL,

    -- UUID that groups messages processed together in one batch
    -- When customer sends "Hi" then "I need help" quickly,
    -- both get the same batch_id so we process them together
    batch_id UUID,

    -- Metadata for tool calls and other context
    -- Example: {"tool_calls": [{"name": "lookup_order", "args": {...}, "result": {...}}]}
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for loading a customer's message history
CREATE INDEX idx_messages_customer ON messages(customer_id, created_at);

-- Index for finding all messages in a batch
CREATE INDEX idx_messages_batch ON messages(batch_id);

-- ============================================================
-- TICKETS TABLE
-- ============================================================
-- Tracks support ticket status for each customer issue.
-- A customer can have multiple tickets over time.
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,

    -- Which customer this ticket belongs to
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,

    -- What KB article (if any) was used to help resolve
    article_id INTEGER REFERENCES knowledge_base(id),

    -- Ticket status
    -- open: issue being handled by agent
    -- resolved: agent resolved with KB article
    -- escalated: handed off to human support
    -- closed: customer confirmed resolved
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'open', 'resolved', 'escalated', 'closed'
    )),

    -- Issue classification
    issue_type VARCHAR(100),  -- e.g., 'billing', 'technical', 'account'
    severity VARCHAR(20),      -- e.g., 'low', 'medium', 'high', 'urgent'

    -- Optional notes (resolution summary, escalation reason, etc.)
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for finding all tickets for a customer
CREATE INDEX idx_tickets_customer ON tickets(customer_id);

-- Index for finding tickets by status (e.g., all escalated tickets)
CREATE INDEX idx_tickets_status ON tickets(status);

-- ============================================================
-- PRODUCTS TABLE (E-Commerce)
-- ============================================================
-- Product catalog for the Macrocenter platform.
CREATE TABLE products (
    id SERIAL PRIMARY KEY,

    -- SKU is the unique product identifier
    sku VARCHAR(50) UNIQUE NOT NULL,

    -- Product details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for searching products by category
CREATE INDEX idx_products_category ON products(category);

-- ============================================================
-- INVENTORY TABLE (E-Commerce)
-- ============================================================
-- Stock levels for each product.
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,

    -- Reference to product
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,

    -- Stock quantity
    quantity INTEGER NOT NULL DEFAULT 0,

    -- Warehouse location (for multi-warehouse support)
    warehouse VARCHAR(100) DEFAULT 'main',

    -- Low stock threshold for alerts
    low_stock_threshold INTEGER DEFAULT 5,

    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for quick inventory lookups by product
CREATE INDEX idx_inventory_product ON inventory(product_id);

-- ============================================================
-- ORDERS TABLE (E-Commerce)
-- ============================================================
-- Customer orders placed through Macrocenter.
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,

    -- Human-readable order number (e.g., "ORD-1001")
    order_number VARCHAR(20) UNIQUE NOT NULL,

    -- Link to customer (can be null for guest orders)
    customer_id INTEGER REFERENCES customers(id),

    -- Order status
    -- pending: just placed, not yet processed
    -- processing: being prepared/packed
    -- shipped: handed to carrier
    -- delivered: confirmed delivery
    -- cancelled: order cancelled before shipping
    -- refunded: money returned to customer
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
    )),

    -- Order total
    total DECIMAL(10,2) NOT NULL,

    -- Shipping details
    shipping_address JSONB,
    tracking_number VARCHAR(100),
    carrier VARCHAR(50),

    -- Customer info for this order (name, email)
    customer_name VARCHAR(200),
    customer_email VARCHAR(255),

    -- Notes from support interactions
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for order lookups by order number
CREATE INDEX idx_orders_number ON orders(order_number);

-- Index for finding orders by customer
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Index for finding orders by status
CREATE INDEX idx_orders_status ON orders(status);

-- ============================================================
-- ORDER_ITEMS TABLE (E-Commerce)
-- ============================================================
-- Line items in each order.
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,

    -- Which order this item belongs to
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

    -- Which product
    product_id INTEGER REFERENCES products(id),

    -- SKU (stored separately for historical record)
    sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,

    -- Quantity and pricing at time of order
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for finding all items in an order
CREATE INDEX idx_order_items_order ON order_items(order_id);
