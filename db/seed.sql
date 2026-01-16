-- seed.sql
-- Sample data for Macrocenter PC Parts store demo.
-- This runs after init.sql.

-- ============================================================
-- KNOWLEDGE BASE ARTICLES (PC Parts)
-- ============================================================

INSERT INTO knowledge_base (article_id, title, content, metadata, status) VALUES
(
    'KB001',
    'CPU & Motherboard Compatibility Guide',
    'Before purchasing, verify CPU and motherboard socket compatibility:

**Intel (Current Gen - LGA 1700)**
- 12th Gen (Alder Lake): i5-12600K, i7-12700K, i9-12900K
- 13th Gen (Raptor Lake): i5-13600K, i7-13700K, i9-13900K
- 14th Gen: i5-14600K, i7-14700K, i9-14900K
- Compatible boards: Z690, Z790, B660, B760, H670, H770

**AMD (Current Gen - AM5)**
- Ryzen 7000 series: 7600X, 7700X, 7800X3D, 7900X, 7950X, 7950X3D
- Compatible boards: X670E, X670, B650E, B650

**AMD (Previous Gen - AM4)**
- Ryzen 5000 series: 5600X, 5800X, 5800X3D, 5900X, 5950X
- Compatible boards: X570, B550, X470, B450 (with BIOS update)

**Common Mistakes:**
- Mixing Intel CPU with AMD motherboard (or vice versa)
- Using DDR4 RAM with DDR5-only motherboard
- Forgetting BIOS update for newer CPUs on older boards

When in doubt, check the motherboard QVL (Qualified Vendor List) on manufacturer website.',
    '{
        "category": "compatibility",
        "tags": ["cpu", "motherboard", "socket", "intel", "amd", "compatibility"],
        "severity_hint": "high"
    }'::jsonb,
    'published'
),
(
    'KB002',
    'GPU Power Requirements & PSU Guide',
    'Ensure your PSU can handle your graphics card:

**NVIDIA GeForce RTX 40 Series**
| GPU | TDP | Recommended PSU | Power Connector |
|-----|-----|-----------------|-----------------|
| RTX 4060 | 115W | 550W | 8-pin |
| RTX 4060 Ti | 160W | 550W | 8-pin |
| RTX 4070 | 200W | 650W | 8-pin |
| RTX 4070 Ti | 285W | 700W | 12VHPWR |
| RTX 4080 | 320W | 750W | 12VHPWR |
| RTX 4090 | 450W | 850W | 12VHPWR |

**AMD Radeon RX 7000 Series**
| GPU | TDP | Recommended PSU | Power Connector |
|-----|-----|-----------------|-----------------|
| RX 7600 | 165W | 550W | 8-pin |
| RX 7700 XT | 245W | 700W | 2x 8-pin |
| RX 7800 XT | 263W | 700W | 2x 8-pin |
| RX 7900 XT | 315W | 750W | 2x 8-pin |
| RX 7900 XTX | 355W | 800W | 2x 8-pin |

**Important Notes:**
- Always leave 100-150W headroom for CPU and other components
- 80+ Gold or better efficiency recommended
- Check GPU length fits your case (measure before buying!)
- 12VHPWR adapters should come with the GPU

For high-end builds (4080/4090 + i9/Ryzen 9), recommend 1000W PSU.',
    '{
        "category": "compatibility",
        "tags": ["gpu", "psu", "power", "wattage", "nvidia", "amd"],
        "severity_hint": "high"
    }'::jsonb,
    'published'
),
(
    'KB003',
    'Return Policy - PC Components',
    'Our return policy for PC components:

**Unopened Items (30 days)**
- Full refund, no questions asked
- Original packaging required
- Return shipping covered by us

**Opened Items (15 days)**
- Must be in original packaging with all accessories
- 15% restocking fee applies
- Item must be in resellable condition
- No thermal paste residue on CPUs/coolers

**Non-Returnable Items:**
- CPUs with bent pins (user damage)
- GPUs with removed/damaged warranty stickers
- Items purchased during flash sales marked "Final Sale"
- Software/digital downloads

**Dead on Arrival (DOA) - 30 days**
- Full refund or replacement, your choice
- We cover return shipping
- Must report within 3 days of delivery
- Photo/video evidence of defect required

**Warranty Claims (30+ days)**
- Contact manufacturer directly
- We can assist with RMA process
- Keep your invoice as proof of purchase

**How to Start a Return:**
1. Contact support with order number
2. Describe reason for return
3. We''ll provide prepaid shipping label
4. Refund processed within 3-5 days of receipt',
    '{
        "category": "returns",
        "tags": ["returns", "refund", "doa", "warranty", "restocking"],
        "severity_hint": "medium"
    }'::jsonb,
    'published'
),
(
    'KB004',
    'Shipping & Handling - Fragile Components',
    'How we ship PC components safely:

**Standard Shipping (3-5 business days)**
- UPS Ground or FedEx Home
- All items shipped in original retail packaging
- Additional padding for GPUs and glass panels
- Free on orders over $99

**Express Shipping (1-2 business days)**
- UPS 2-Day or FedEx Express
- $14.99 flat rate under 10 lbs
- Same protective packaging

**Signature Required:**
Orders over $300 require signature confirmation. This protects against:
- Porch theft (GPUs are targets!)
- Delivery disputes
- "Not delivered" claims

**GPU Shipping:**
- Always shipped in anti-static bags
- GPU box placed inside larger box with padding
- Fragile stickers applied

**Tracking:**
- Tracking number emailed within 24 hours of shipping
- Real-time updates via carrier website
- Delivery notifications available

**Damaged in Shipping:**
1. Document damage with photos BEFORE opening
2. Contact us within 48 hours
3. Keep all packaging materials
4. We''ll file carrier claim and send replacement

**International Shipping:**
Currently shipping to US and Canada only. International orders subject to:
- Customs fees (buyer responsibility)
- Longer delivery times (7-14 days)
- No express option available',
    '{
        "category": "shipping",
        "tags": ["shipping", "delivery", "tracking", "fragile", "damaged"],
        "severity_hint": "low"
    }'::jsonb,
    'published'
),
(
    'KB005',
    'PC Build Troubleshooting Guide',
    'Common issues and solutions for new builds:

**No POST / No Display**
1. Reseat RAM - remove and reinstall firmly (click on both sides)
2. Check CPU power (4+4 or 8-pin connector)
3. Check GPU power (all connectors seated)
4. Try one RAM stick at a time
5. Reset CMOS (remove battery 30 sec or use jumper)
6. Check for bent CPU pins (AMD) or socket damage (Intel)

**Boot Loops / Restarts**
- Often RAM XMP issue - disable XMP in BIOS first
- Check CPU cooler is mounted properly (thermal throttling)
- Verify PSU wattage is sufficient

**GPU Not Detected**
1. Reseat GPU in PCIe slot
2. Check power connectors (all plugged in?)
3. Try different PCIe slot if available
4. Update motherboard BIOS
5. Check display cable is plugged into GPU, not motherboard

**High Temperatures**
- Remove plastic peel from cooler base (common mistake!)
- Reapply thermal paste (pea-sized amount)
- Check case airflow (intake front, exhaust rear/top)
- Verify all fans spinning

**RAM Not Running at Rated Speed**
1. Enable XMP/EXPO in BIOS
2. Check motherboard QVL for compatibility
3. Update BIOS to latest version
4. Try different DIMM slots (check manual for optimal config)

**Still Stuck?**
Escalate to our support team with:
- Full parts list
- Photo of build (inside case)
- Description of symptoms
- Any error codes/beeps',
    '{
        "category": "technical",
        "tags": ["troubleshooting", "no-post", "build", "problems", "help"],
        "severity_hint": "medium"
    }'::jsonb,
    'published'
),
(
    'KB006',
    'Warranty & RMA Information',
    'Warranty coverage for PC components:

**Manufacturer Warranties:**
| Component | Typical Warranty |
|-----------|-----------------|
| GPUs | 3 years (register with manufacturer) |
| CPUs | 3 years (Intel/AMD) |
| Motherboards | 3 years |
| RAM | Lifetime (most brands) |
| SSDs | 3-5 years |
| PSUs | 5-10 years (brand dependent) |
| Cases | 1-2 years |
| Coolers | 2-6 years |

**How to File a Warranty Claim:**
1. Check if item is within warranty period
2. Contact manufacturer directly (faster than going through us)
3. Provide proof of purchase (we can resend invoice)
4. Follow their RMA process

**We Can Help With:**
- Providing purchase documentation
- Contacting manufacturer on your behalf
- Troubleshooting to confirm defect
- Cross-shipping replacement (for premium customers)

**What Voids Warranty:**
- Physical damage (dropped, bent pins)
- Water/liquid damage
- Overclocking damage (varies by manufacturer)
- Removed warranty stickers
- Using unofficial cooling solutions

**Extended Warranty:**
We offer extended protection plans:
- 2-year extension: 10% of item price
- Covers accidental damage
- No deductibles
- Cross-ship replacements

Contact support to add extended warranty within 30 days of purchase.',
    '{
        "category": "warranty",
        "tags": ["warranty", "rma", "claim", "manufacturer", "protection"],
        "severity_hint": "medium"
    }'::jsonb,
    'published'
);

-- ============================================================
-- PC PARTS PRODUCTS
-- ============================================================

INSERT INTO products (sku, name, description, price, category) VALUES
-- GPUs
('GPU-RTX4090', 'NVIDIA GeForce RTX 4090 24GB', 'Flagship GPU. 24GB GDDR6X, 450W TDP, requires 850W+ PSU.', 1599.99, 'gpu'),
('GPU-RTX4080', 'NVIDIA GeForce RTX 4080 16GB', 'High-end GPU. 16GB GDDR6X, 320W TDP, requires 750W+ PSU.', 1199.99, 'gpu'),
('GPU-RTX4070TI', 'NVIDIA GeForce RTX 4070 Ti 12GB', 'Performance GPU. 12GB GDDR6X, 285W TDP, requires 700W+ PSU.', 799.99, 'gpu'),
('GPU-RTX4070', 'NVIDIA GeForce RTX 4070 12GB', 'Sweet spot GPU. 12GB GDDR6X, 200W TDP, requires 650W+ PSU.', 549.99, 'gpu'),
('GPU-RTX4060TI', 'NVIDIA GeForce RTX 4060 Ti 8GB', 'Mid-range GPU. 8GB GDDR6, 160W TDP, requires 550W+ PSU.', 399.99, 'gpu'),
('GPU-RX7900XTX', 'AMD Radeon RX 7900 XTX 24GB', 'AMD flagship. 24GB GDDR6, 355W TDP, requires 800W+ PSU.', 949.99, 'gpu'),
('GPU-RX7800XT', 'AMD Radeon RX 7800 XT 16GB', 'AMD performance. 16GB GDDR6, 263W TDP, requires 700W+ PSU.', 499.99, 'gpu'),

-- CPUs
('CPU-I9-14900K', 'Intel Core i9-14900K', '24 cores (8P+16E), 6.0GHz boost, LGA 1700, 253W TDP.', 549.99, 'cpu'),
('CPU-I7-14700K', 'Intel Core i7-14700K', '20 cores (8P+12E), 5.6GHz boost, LGA 1700, 253W TDP.', 409.99, 'cpu'),
('CPU-I5-14600K', 'Intel Core i5-14600K', '14 cores (6P+8E), 5.3GHz boost, LGA 1700, 181W TDP.', 319.99, 'cpu'),
('CPU-R9-7950X3D', 'AMD Ryzen 9 7950X3D', '16 cores, 5.7GHz boost, AM5, 3D V-Cache, best for gaming.', 699.99, 'cpu'),
('CPU-R7-7800X3D', 'AMD Ryzen 7 7800X3D', '8 cores, 5.0GHz boost, AM5, 3D V-Cache, gaming king.', 449.99, 'cpu'),
('CPU-R5-7600X', 'AMD Ryzen 5 7600X', '6 cores, 5.3GHz boost, AM5, great value.', 249.99, 'cpu'),

-- Motherboards
('MB-Z790-HERO', 'ASUS ROG Maximus Z790 Hero', 'Premium Intel Z790, DDR5, WiFi 6E, 2.5GbE, LGA 1700.', 629.99, 'motherboard'),
('MB-Z790-STRIX', 'ASUS ROG Strix Z790-E Gaming', 'High-end Intel Z790, DDR5, WiFi 6E, LGA 1700.', 399.99, 'motherboard'),
('MB-B760-TOMAHAWK', 'MSI MAG B760 Tomahawk WiFi', 'Mid-range Intel B760, DDR5, WiFi 6E, LGA 1700.', 199.99, 'motherboard'),
('MB-X670E-HERO', 'ASUS ROG Crosshair X670E Hero', 'Premium AMD X670E, DDR5, WiFi 6E, AM5.', 699.99, 'motherboard'),
('MB-X670E-STRIX', 'ASUS ROG Strix X670E-E Gaming', 'High-end AMD X670E, DDR5, WiFi 6E, AM5.', 449.99, 'motherboard'),
('MB-B650-TOMAHAWK', 'MSI MAG B650 Tomahawk WiFi', 'Mid-range AMD B650, DDR5, WiFi 6E, AM5.', 229.99, 'motherboard'),

-- RAM
('RAM-DDR5-32-6000', 'G.Skill Trident Z5 RGB 32GB (2x16GB) DDR5-6000', 'High-speed DDR5, CL30, Intel XMP 3.0.', 149.99, 'memory'),
('RAM-DDR5-32-5600', 'Corsair Vengeance 32GB (2x16GB) DDR5-5600', 'DDR5 kit, CL36, black heatspreader.', 119.99, 'memory'),
('RAM-DDR5-64-6000', 'G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5-6000', 'High-capacity DDR5, CL30, for workstations.', 279.99, 'memory'),

-- Storage
('SSD-990PRO-2TB', 'Samsung 990 Pro 2TB NVMe', 'PCIe 4.0, 7450/6900 MB/s read/write, top tier.', 179.99, 'storage'),
('SSD-990PRO-1TB', 'Samsung 990 Pro 1TB NVMe', 'PCIe 4.0, 7450/6900 MB/s read/write.', 109.99, 'storage'),
('SSD-SN850X-2TB', 'WD Black SN850X 2TB NVMe', 'PCIe 4.0, 7300/6600 MB/s, great for gaming.', 149.99, 'storage'),
('SSD-SN850X-1TB', 'WD Black SN850X 1TB NVMe', 'PCIe 4.0, 7300/6600 MB/s.', 89.99, 'storage'),

-- PSUs
('PSU-RM1000X', 'Corsair RM1000x 1000W', '80+ Gold, fully modular, 10-year warranty.', 189.99, 'psu'),
('PSU-RM850X', 'Corsair RM850x 850W', '80+ Gold, fully modular, 10-year warranty.', 149.99, 'psu'),
('PSU-RM750X', 'Corsair RM750x 750W', '80+ Gold, fully modular, 10-year warranty.', 119.99, 'psu'),
('PSU-FOCUS-850', 'Seasonic Focus GX-850 850W', '80+ Gold, fully modular, 10-year warranty.', 139.99, 'psu'),

-- Cases
('CASE-5000D', 'Corsair 5000D Airflow', 'Mid-tower, excellent airflow, tempered glass.', 174.99, 'case'),
('CASE-4000D', 'Corsair 4000D Airflow', 'Mid-tower, great airflow, compact.', 104.99, 'case'),
('CASE-H7-FLOW', 'NZXT H7 Flow', 'Mid-tower, perforated front panel, clean design.', 129.99, 'case'),
('CASE-O11-EVO', 'Lian Li O11 Dynamic EVO', 'Dual-chamber, show build, great for custom loops.', 169.99, 'case'),

-- Coolers
('COOL-AK620', 'DeepCool AK620', 'Dual-tower air cooler, rivals 280mm AIOs.', 64.99, 'cooler'),
('COOL-NH-D15', 'Noctua NH-D15', 'Premium dual-tower, best air cooler, quiet.', 109.99, 'cooler'),
('COOL-H150I', 'Corsair H150i Elite LCD', '360mm AIO, LCD display, great cooling.', 289.99, 'cooler'),
('COOL-X63', 'NZXT Kraken X63', '280mm AIO, infinity mirror, CAM software.', 159.99, 'cooler');

-- ============================================================
-- INVENTORY WITH REALISTIC SCENARIOS
-- ============================================================

INSERT INTO inventory (product_id, quantity, warehouse, low_stock_threshold)
SELECT id,
    CASE
        -- GPUs: notoriously hard to stock
        WHEN sku = 'GPU-RTX4090' THEN 2      -- Very limited
        WHEN sku = 'GPU-RTX4080' THEN 5      -- Low stock
        WHEN sku = 'GPU-RTX4070TI' THEN 0    -- Out of stock!
        WHEN sku = 'GPU-RTX4070' THEN 12     -- Good stock
        WHEN sku = 'GPU-RTX4060TI' THEN 25   -- Plenty
        WHEN sku = 'GPU-RX7900XTX' THEN 3    -- Limited
        WHEN sku = 'GPU-RX7800XT' THEN 8     -- Low
        -- CPUs: generally available
        WHEN sku LIKE 'CPU-%' THEN 20
        -- Motherboards: varies
        WHEN sku = 'MB-Z790-HERO' THEN 4
        WHEN sku = 'MB-X670E-HERO' THEN 3
        WHEN sku LIKE 'MB-%' THEN 15
        -- RAM: usually good stock
        WHEN sku LIKE 'RAM-%' THEN 30
        -- Storage: good stock
        WHEN sku LIKE 'SSD-%' THEN 40
        -- PSUs: good stock
        WHEN sku LIKE 'PSU-%' THEN 25
        -- Cases: bulky, moderate stock
        WHEN sku LIKE 'CASE-%' THEN 15
        -- Coolers: good stock
        WHEN sku LIKE 'COOL-%' THEN 20
        ELSE 10
    END,
    'main',
    CASE
        WHEN sku LIKE 'GPU-%' THEN 3  -- Low threshold for GPUs (they're hard to get)
        ELSE 5
    END
FROM products;

-- ============================================================
-- SAMPLE CUSTOMERS
-- ============================================================

INSERT INTO customers (phone_number, email, first_name, last_name, company_name, account_tier, extracted_data) VALUES
('+15551111111', 'alex.chen@gmail.com', 'Alex', 'Chen', NULL, 'standard', '{"builds": 2, "lifetime_value": 2400}'::jsonb),
('+15559876543', 'marcus.johnson@techcorp.com', 'Marcus', 'Johnson', 'TechCorp Solutions', 'pro', '{"builds": 5, "lifetime_value": 8500}'::jsonb),
('+15555550123', 'sarah.kim@gmail.com', 'Sarah', 'Kim', NULL, 'standard', '{"builds": 1, "lifetime_value": 1200}'::jsonb);

-- ============================================================
-- SAMPLE ORDERS
-- ============================================================

INSERT INTO orders (order_number, customer_id, status, total, shipping_address, tracking_number, carrier, customer_name, customer_email, notes, created_at) VALUES
-- Delivered high-end GPU order
(
    'ORD-1001',
    1,
    'delivered',
    1599.99,
    '{"street": "742 Evergreen Terrace", "city": "San Jose", "state": "CA", "zip": "95101"}'::jsonb,
    '1Z999AA10123456784',
    'UPS',
    'Alex Chen',
    'alex.chen@gmail.com',
    'RTX 4090 - Signature confirmed by A. Chen',
    NOW() - INTERVAL '5 days'
),
-- Shipped CPU + Motherboard combo
(
    'ORD-1002',
    1,
    'shipped',
    859.98,
    '{"street": "742 Evergreen Terrace", "city": "San Jose", "state": "CA", "zip": "95101"}'::jsonb,
    '9400111899223456789012',
    'USPS',
    'Alex Chen',
    'alex.chen@gmail.com',
    'i7-14700K + Z790 Strix - Building new rig',
    NOW() - INTERVAL '2 days'
),
-- Processing full build for business customer
(
    'ORD-1003',
    2,
    'processing',
    3249.94,
    '{"street": "100 Tech Park Drive", "city": "Austin", "state": "TX", "zip": "78701"}'::jsonb,
    NULL,
    NULL,
    'Marcus Johnson',
    'marcus.johnson@techcorp.com',
    'Workstation build: R9 7950X3D + RTX 4080 + 64GB RAM - Priority customer',
    NOW() - INTERVAL '1 day'
),
-- Cancelled - ordered wrong socket
(
    'ORD-1004',
    3,
    'cancelled',
    449.99,
    '{"street": "456 Oak Street", "city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb,
    NULL,
    NULL,
    'Sarah Kim',
    'sarah.kim@gmail.com',
    'CANCELLED: Customer ordered AM5 motherboard for Intel CPU. Refunded.',
    NOW() - INTERVAL '3 days'
),
-- Pending new order
(
    'ORD-1005',
    3,
    'pending',
    1049.97,
    '{"street": "456 Oak Street", "city": "Seattle", "state": "WA", "zip": "98101"}'::jsonb,
    NULL,
    NULL,
    'Sarah Kim',
    'sarah.kim@gmail.com',
    'Corrected order: 7800X3D + B650 Tomahawk + 32GB RAM',
    NOW()
),
-- Refunded - DOA component
(
    'ORD-1006',
    2,
    'refunded',
    179.99,
    '{"street": "100 Tech Park Drive", "city": "Austin", "state": "TX", "zip": "78701"}'::jsonb,
    '1Z999BB20234567891',
    'UPS',
    'Marcus Johnson',
    'marcus.johnson@techcorp.com',
    'DOA: Samsung 990 Pro showing read errors out of box. Full refund issued.',
    NOW() - INTERVAL '10 days'
);

-- ============================================================
-- ORDER ITEMS
-- ============================================================

-- ORD-1001: RTX 4090
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'GPU-RTX4090', 'NVIDIA GeForce RTX 4090 24GB', 1, 1599.99
FROM orders o, products p WHERE o.order_number = 'ORD-1001' AND p.sku = 'GPU-RTX4090';

-- ORD-1002: i7-14700K + Z790 Strix
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'CPU-I7-14700K', 'Intel Core i7-14700K', 1, 409.99
FROM orders o, products p WHERE o.order_number = 'ORD-1002' AND p.sku = 'CPU-I7-14700K';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'MB-Z790-STRIX', 'ASUS ROG Strix Z790-E Gaming', 1, 449.99
FROM orders o, products p WHERE o.order_number = 'ORD-1002' AND p.sku = 'MB-Z790-STRIX';

-- ORD-1003: Full workstation build
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'CPU-R9-7950X3D', 'AMD Ryzen 9 7950X3D', 1, 699.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'CPU-R9-7950X3D';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'GPU-RTX4080', 'NVIDIA GeForce RTX 4080 16GB', 1, 1199.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'GPU-RTX4080';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'MB-X670E-STRIX', 'ASUS ROG Strix X670E-E Gaming', 1, 449.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'MB-X670E-STRIX';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'RAM-DDR5-64-6000', 'G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5-6000', 1, 279.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'RAM-DDR5-64-6000';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'PSU-RM850X', 'Corsair RM850x 850W', 1, 149.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'PSU-RM850X';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SSD-990PRO-2TB', 'Samsung 990 Pro 2TB NVMe', 1, 179.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'SSD-990PRO-2TB';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'CASE-5000D', 'Corsair 5000D Airflow', 1, 174.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'CASE-5000D';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'COOL-H150I', 'Corsair H150i Elite LCD', 1, 289.99
FROM orders o, products p WHERE o.order_number = 'ORD-1003' AND p.sku = 'COOL-H150I';

-- ORD-1004: Wrong socket order (cancelled)
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'MB-X670E-STRIX', 'ASUS ROG Strix X670E-E Gaming', 1, 449.99
FROM orders o, products p WHERE o.order_number = 'ORD-1004' AND p.sku = 'MB-X670E-STRIX';

-- ORD-1005: Corrected AMD build
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'CPU-R7-7800X3D', 'AMD Ryzen 7 7800X3D', 1, 449.99
FROM orders o, products p WHERE o.order_number = 'ORD-1005' AND p.sku = 'CPU-R7-7800X3D';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'MB-B650-TOMAHAWK', 'MSI MAG B650 Tomahawk WiFi', 1, 229.99
FROM orders o, products p WHERE o.order_number = 'ORD-1005' AND p.sku = 'MB-B650-TOMAHAWK';

INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'RAM-DDR5-32-6000', 'G.Skill Trident Z5 RGB 32GB (2x16GB) DDR5-6000', 1, 149.99
FROM orders o, products p WHERE o.order_number = 'ORD-1005' AND p.sku = 'RAM-DDR5-32-6000';

-- ORD-1006: DOA SSD (refunded)
INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, unit_price)
SELECT o.id, p.id, 'SSD-990PRO-2TB', 'Samsung 990 Pro 2TB NVMe', 1, 179.99
FROM orders o, products p WHERE o.order_number = 'ORD-1006' AND p.sku = 'SSD-990PRO-2TB';

-- ============================================================
-- VERIFY DATA
-- ============================================================
DO $$
DECLARE
    article_count INTEGER;
    product_count INTEGER;
    order_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO article_count FROM knowledge_base;
    SELECT COUNT(*) INTO product_count FROM products;
    SELECT COUNT(*) INTO order_count FROM orders;
    RAISE NOTICE 'SEED DATA LOADED: % KB articles, % products, % orders',
        article_count, product_count, order_count;
END $$;
