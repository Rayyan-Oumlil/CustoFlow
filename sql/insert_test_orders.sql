-- ============================================================================
-- Script to insert 5 additional test orders into the orders table
-- Run this script in Supabase SQL Editor to add test data
-- ============================================================================

-- Insert 5 new test orders with different statuses and customers
INSERT INTO public.orders (
    order_id,
    customer_id,
    status,
    total,
    items,
    notes,
    tracking_number,
    estimated_delivery,
    created_at,
    updated_at
) VALUES
-- Order 1: Processing order for cust_001
(
    '66666',
    'cust_001',
    'processing',
    199.98,
    '[
        {"name": "Wireless Mouse", "quantity": 2, "price": 29.99},
        {"name": "Keyboard Wrist Rest", "quantity": 1, "price": 19.99},
        {"name": "USB Hub", "quantity": 1, "price": 24.99}
    ]'::jsonb,
    '[]'::jsonb,
    NULL,
    '2024-02-05',
    NOW(),
    NOW()
),

-- Order 2: Shipped order for cust_002
(
    '77777',
    'cust_002',
    'shipped',
    89.97,
    '[
        {"name": "Desk Lamp LED", "quantity": 1, "price": 39.99},
        {"name": "Cable Management Kit", "quantity": 1, "price": 19.99},
        {"name": "Desk Organizer", "quantity": 1, "price": 29.99}
    ]'::jsonb,
    '[]'::jsonb,
    'TRACK777777',
    '2024-01-30',
    NOW() - INTERVAL '3 days',
    NOW() - INTERVAL '1 day'
),

-- Order 3: Delivering order for cust_003
(
    '88888',
    'cust_003',
    'delivering',
    249.99,
    '[
        {"name": "Standing Desk Converter", "quantity": 1, "price": 199.99},
        {"name": "Anti-Fatigue Mat", "quantity": 1, "price": 49.99}
    ]'::jsonb,
    '[]'::jsonb,
    'TRACK888888',
    '2024-01-28',
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '2 days'
),

-- Order 4: Delivery soon order for cust_004
(
    '99999',
    'cust_004',
    'delivery_soon',
    159.98,
    '[
        {"name": "Noise Cancelling Headphones", "quantity": 1, "price": 129.99},
        {"name": "Headphone Stand", "quantity": 1, "price": 29.99}
    ]'::jsonb,
    '[]'::jsonb,
    'TRACK999999',
    '2024-01-26',
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '1 day'
),

-- Order 5: Delivered order for cust_001
(
    '10000',
    'cust_001',
    'delivered',
    179.97,
    '[
        {"name": "Ergonomic Chair", "quantity": 1, "price": 149.99},
        {"name": "Lumbar Support Pillow", "quantity": 1, "price": 29.99}
    ]'::jsonb,
    '[]'::jsonb,
    'TRACK100000',
    '2024-01-20',
    NOW() - INTERVAL '10 days',
    NOW() - INTERVAL '3 days'
)

ON CONFLICT (order_id) DO UPDATE SET
    customer_id = EXCLUDED.customer_id,
    status = EXCLUDED.status,
    total = EXCLUDED.total,
    items = EXCLUDED.items,
    notes = EXCLUDED.notes,
    tracking_number = EXCLUDED.tracking_number,
    estimated_delivery = EXCLUDED.estimated_delivery,
    updated_at = EXCLUDED.updated_at;

-- Verify the insert
SELECT 
    order_id,
    customer_id,
    status,
    total,
    jsonb_array_length(items) as item_count,
    tracking_number,
    estimated_delivery
FROM public.orders
WHERE order_id IN ('66666', '77777', '88888', '99999', '10000')
ORDER BY order_id;

