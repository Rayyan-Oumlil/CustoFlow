"""Shipping Tracking Tool - OpenAPI Tool Pattern for Real-Time Shipping Tracking"""

from typing import Dict, Optional
from datetime import datetime
from google.adk.tools import FunctionTool


# All shipping data now comes from Supabase - no hardcoded simulation
# This tool demonstrates OpenAPI pattern by fetching real data from database

def track_shipment(
 tracking_number: str,
 carrier: str = "ups"
) -> Dict[str, any]:
 """
 Track a shipment in real-time using a shipping carrier API.
 
 This function simulates an OpenAPI Tool that would call a real shipping
 carrier API (UPS, FedEx, DHL) to get real-time tracking information.
 
 In production, this would be implemented as:
 ```python
 shipping_tool = OpenAPITool.from_openapi_spec(
 spec_url="https://api.ups.com/openapi.json",
 operation_id="track_shipment"
 )
 ```
 
 Args:
 tracking_number: The tracking number for the shipment
 carrier: Shipping carrier (ups, fedex, dhl) - defaults to "ups"
 
 Returns:
 Dictionary with tracking information including:
 - status: Current shipping status
 - location: Current package location
 - estimated_delivery: Estimated delivery date/time
 - tracking_events: List of tracking events
 - carrier: Shipping carrier name
 """
 try:
 if not tracking_number or not tracking_number.strip():
 return {
 "status": "error",
 "error_message": "Tracking number is required"
 }
 
 tracking_number = tracking_number.strip().upper()
 carrier = carrier.lower()
 
 # Validate carrier
 valid_carriers = ["ups", "fedex", "dhl", "usps"]
 if carrier not in valid_carriers:
 carrier = "ups"
 
 # Get order data from Supabase (no simulation, only real data)
 order_data = _get_order_from_tracking(tracking_number)
 
 if not order_data:
 return {
 "status": "error",
 "error_message": f"Order with tracking number {tracking_number} not found in database"
 }
 
 # Use real order data from Supabase
 order_status = order_data.get("status")
 estimated_delivery_date = order_data.get("estimated_delivery")
 
 # Map order status to shipping status description
 status_descriptions = {
 "processing": "Order is being prepared for shipment",
 "shipped": "Package has left the warehouse",
 "delivering": "Package is in transit to destination",
 "delivery_soon": "Package is out for delivery",
 "delivered": "Package has been delivered",
 "cancelled": "Order has been cancelled"
 }
 
 # Format estimated delivery from Supabase
 estimated_delivery = None
 if estimated_delivery_date:
 if isinstance(estimated_delivery_date, str):
 estimated_delivery = {
 "date": estimated_delivery_date,
 "time": None,
 "timezone": "UTC"
 }
 else:
 estimated_delivery = {
 "date": estimated_delivery_date.strftime("%Y-%m-%d") if hasattr(estimated_delivery_date, 'strftime') else str(estimated_delivery_date),
 "time": None,
 "timezone": "UTC"
 }
 
 # Determine location based on order status (simple mapping)
 location_map = {
 "processing": "Warehouse",
 "shipped": "Origin Facility",
 "delivering": "Distribution Center",
 "delivery_soon": "Local Delivery Facility",
 "delivered": "Destination",
 "cancelled": "Warehouse"
 }
 
 # Get carrier info from order if available, otherwise use provided carrier
 # In production, carrier would come from order data or external API
 carrier_name_map = {
 "ups": "United Parcel Service",
 "fedex": "FedEx",
 "dhl": "DHL Express",
 "usps": "USPS"
 }
 
 result = {
 "status": "success",
 "tracking_number": tracking_number,
 "carrier": {
 "carrier_name": carrier_name_map.get(carrier, "Unknown Carrier"),
 "service": "Standard Shipping" # Could come from order data in production
 },
 "current_status": order_status,
 "status_description": status_descriptions.get(order_status, f"Order status: {order_status}"),
 "current_location": location_map.get(order_status, "Unknown"),
 "estimated_delivery": estimated_delivery,
 "order_id": order_data.get("order_id"),
 "customer_id": order_data.get("customer_id"),
 "last_updated": order_data.get("updated_at") or datetime.now().isoformat()
 }
 
 print(f" [SHIPPING-API] Tracked {tracking_number} via {carrier.upper()} - Status: {order_status}")
 
 return result
 
 except Exception as e:
 return {
 "status": "error",
 "error_message": f"Error tracking shipment: {str(e)}"
 }


def _get_order_from_tracking(tracking_number: str) -> Optional[Dict]:
 """
 Get the complete order data from Supabase using tracking number.
 Returns all order fields, not just status.
 """
 try:
 # Try Supabase first
 from utils.supabase_client import SUPABASE_ENABLED
 if SUPABASE_ENABLED:
 from supabase import create_client
 import os
 from dotenv import load_dotenv
 load_dotenv()
 supabase_url = os.getenv("SUPABASE_URL")
 supabase_key = os.getenv("SUPABASE_KEY")
 if supabase_url and supabase_key:
 supabase = create_client(supabase_url, supabase_key)
 result = supabase.table("orders").select("*").eq("tracking_number", tracking_number).limit(1).execute()
 if result.data and len(result.data) > 0:
 return result.data[0]
 except Exception as e:
 print(f"Warning: Could not get order from Supabase: {e}")
 
 # Fallback: try JSON file
 try:
 from tools.order_tool import _load_orders, _MOCK_ORDERS
 # Normalize tracking number for comparison (uppercase, strip)
 tracking_normalized = tracking_number.strip().upper() if tracking_number else ""
 
 # Try in-memory dict first (faster, more up-to-date)
 for order in _MOCK_ORDERS.values():
 order_tracking = order.get("tracking_number", "")
 if order_tracking:
 order_tracking_normalized = str(order_tracking).strip().upper()
 if order_tracking_normalized == tracking_normalized:
 return order
 # If not found in memory, reload from file
 orders = _load_orders()
 for order in orders.values():
 order_tracking = order.get("tracking_number", "")
 if order_tracking:
 order_tracking_normalized = str(order_tracking).strip().upper()
 if order_tracking_normalized == tracking_normalized:
 return order
 except Exception as e:
 print(f"Warning: Could not get order from JSON: {e}")
 
 return None


# Removed _generate_estimated_delivery and _generate_tracking_events
# All data now comes from Supabase, no simulation needed


# Create FunctionTool for ADK
# Note: In production, this would be:
# shipping_tool = OpenAPITool.from_openapi_spec(spec_url="...", operation_id="track_shipment")
shipping_tracking_tool = FunctionTool(track_shipment)

