"""
Script to insert test orders into Supabase
Run this script to easily add test orders without using the Supabase UI
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client
    from datetime import datetime, date
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Test orders data
    test_orders = [
        {
            "order_id": "12345",
            "customer_id": "cust_001",
            "status": "shipped",
            "total": 99.99,
            "items": [
                {
                    "name": "Wireless Headphones",
                    "quantity": 1,
                    "price": 99.99
                }
            ],
            "tracking_number": "TRACK123456",
            "estimated_delivery": "2024-01-22",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "order_id": "67890",
            "customer_id": "cust_002",
            "status": "processing",
            "total": 75.97,
            "items": [
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
            ],
            "tracking_number": None,
            "estimated_delivery": "2024-01-27",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "order_id": "11111",
            "customer_id": "cust_003",
            "status": "delivered",
            "total": 149.99,
            "items": [
                {
                    "name": "Mechanical Keyboard",
                    "quantity": 1,
                    "price": 149.99
                }
            ],
            "tracking_number": "TRACK789012",
            "estimated_delivery": "2024-01-17",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "order_id": "22222",
            "customer_id": "cust_001",
            "status": "cancelled",
            "total": 19.99,
            "items": [
                {
                    "name": "Mouse Pad",
                    "quantity": 1,
                    "price": 19.99
                }
            ],
            "tracking_number": None,
            "estimated_delivery": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "order_id": "10262006",
            "customer_id": "cust_004",
            "status": "processing",
            "total": 300.0,
            "items": [
                {
                    "name": "Ryzen 5 9600x",
                    "quantity": 2,
                    "price": 150.0
                }
            ],
            "tracking_number": "Track20061026",
            "estimated_delivery": "2025-11-20",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    print("=" * 70)
    print("Inserting test orders into Supabase...")
    print("=" * 70)
    print()
    
    inserted = 0
    updated = 0
    errors = 0
    
    for order in test_orders:
        try:
            # Try to insert, if conflict (order_id exists), update instead
            result = supabase.table("orders").upsert(order).execute()
            
            # Check if it was inserted or updated
            existing = supabase.table("orders").select("order_id").eq("order_id", order["order_id"]).execute()
            if existing.data:
                updated += 1
                print(f"✅ Updated order {order['order_id']} - {order['customer_id']} - {order['status']}")
            else:
                inserted += 1
                print(f"✅ Inserted order {order['order_id']} - {order['customer_id']} - {order['status']}")
        except Exception as e:
            errors += 1
            print(f"❌ Error inserting order {order['order_id']}: {e}")
    
    print()
    print("=" * 70)
    print("Summary:")
    print(f"  ✅ Inserted: {inserted}")
    print(f"  🔄 Updated: {updated}")
    print(f"  ❌ Errors: {errors}")
    print("=" * 70)
    
    # Verify orders
    print()
    print("Verifying orders in database...")
    try:
        all_orders = supabase.table("orders").select("order_id, customer_id, status, total").execute()
        print(f"✅ Total orders in database: {len(all_orders.data)}")
        for order in all_orders.data:
            print(f"   - {order['order_id']}: {order['customer_id']} - {order['status']} - ${order['total']}")
    except Exception as e:
        print(f"⚠️  Error verifying orders: {e}")

except ImportError:
    print("❌ Error: supabase-py is not installed")
    print("   Install it with: pip install supabase")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

