-- Insert test orders into Supabase
-- Run this script to add test orders for testing

-- Delete existing test orders first (optional - comment out if you want to keep existing orders)
-- DELETE FROM orders WHERE order_id IN ('12345', '67890', '11111', '22222', '10262006');

-- Insert test orders
INSERT INTO orders (order_id, customer_id, status, total, items, tracking_number, estimated_delivery, created_at, updated_at)
VALUES
    (
        '12345',
        'cust_001',
        'shipped',
        99.99,
        '[
            {
                "name": "Wireless Headphones",
                "quantity": 1,
                "price": 99.99
            }
        ]'::jsonb,
        'TRACK123456',
        '2024-01-22',
        NOW(),
        NOW()
    ),
    (
        '67890',
        'cust_002',
        'processing',
        75.97,
        '[
            {
                "name": "Laptop Stand",
                "quantity": 1,
                "price": 49.99
            },
            {
                "name": "USB-C Cable",
                "quantity": 2,
                "price": 12.99
            }
        ]'::jsonb,
        NULL,
        '2024-01-27',
        NOW(),
        NOW()
    ),
    (
        '11111',
        'cust_003',
        'delivered',
        149.99,
        '[
            {
                "name": "Mechanical Keyboard",
                "quantity": 1,
                "price": 149.99
            }
        ]'::jsonb,
        'TRACK789012',
        '2024-01-17',
        NOW(),
        NOW()
    ),
    (
        '22222',
        'cust_001',
        'cancelled',
        19.99,
        '[
            {
                "name": "Mouse Pad",
                "quantity": 1,
                "price": 19.99
            }
        ]'::jsonb,
        NULL,
        NULL,
        NOW(),
        NOW()
    ),
    (
        '10262006',
        'cust_004',
        'processing',
        300.0,
        '[
            {
                "name": "Ryzen 5 9600x",
                "quantity": 2,
                "price": 150.0
            }
        ]'::jsonb,
        'Track20061026',
        '2025-11-20',
        NOW(),
        NOW()
    )
ON CONFLICT (order_id) DO UPDATE
SET
    customer_id = EXCLUDED.customer_id,
    status = EXCLUDED.status,
    total = EXCLUDED.total,
    items = EXCLUDED.items,
    tracking_number = EXCLUDED.tracking_number,
    estimated_delivery = EXCLUDED.estimated_delivery,
    updated_at = NOW();

-- Verify orders were inserted
SELECT 
    order_id,
    customer_id,
    status,
    total,
    created_at
FROM orders
ORDER BY created_at DESC;

