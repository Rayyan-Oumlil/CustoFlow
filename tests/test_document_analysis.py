"""
Test script for document analysis functionality.

This script tests the document analysis tool with sample images.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.document_analysis_tool import analyze_document, analyze_receipt_for_order, analyze_product_photo


def test_document_analysis():
    """Test document analysis with a sample image."""
    
    print("🧪 Testing Document Analysis Tool\n")
    
    # Check if we have a test image
    test_image_path = Path(__file__).parent.parent / "tests" / "test_receipt.jpg"
    
    if not test_image_path.exists():
        print("⚠️  No test image found. Creating a simple test...")
        print("\nTo test with a real image:")
        print("1. Place a receipt/invoice image in tests/test_receipt.jpg")
        print("2. Run this test again")
        print("\nOr test via API:")
        print("1. Start the server: python -m api.server")
        print("2. Use curl or Postman to POST to /documents/analyze")
        return
    
    try:
        # Read test image
        with open(test_image_path, "rb") as f:
            image_data = f.read()
        
        print(f"📄 Testing with: {test_image_path.name} ({len(image_data)} bytes)\n")
        
        # Test 1: Auto analysis
        print("Test 1: Auto analysis")
        print("-" * 50)
        result = analyze_document(
            file_data=image_data,
            file_type="image/jpeg",
            analysis_type="auto"
        )
        
        if result.get("status") == "success":
            print("✅ Analysis successful!")
            print(f"Document type: {result.get('document_type')}")
            print(f"Summary: {result.get('summary')}")
            if result.get("extracted_data"):
                print(f"Extracted data: {result.get('extracted_data')}")
        else:
            print(f"❌ Analysis failed: {result.get('error_message')}")
        
        print("\n")
        
        # Test 2: Receipt analysis
        print("Test 2: Receipt analysis")
        print("-" * 50)
        result = analyze_receipt_for_order(
            file_data=image_data,
            file_type="image/jpeg"
        )
        
        if result.get("status") == "success":
            print("✅ Receipt analysis successful!")
            extracted = result.get("extracted_data", {})
            if extracted.get("order_id"):
                print(f"📦 Order ID found: {extracted['order_id']}")
            if extracted.get("amount"):
                print(f"💰 Amount: ${extracted['amount']}")
            if extracted.get("date"):
                print(f"📅 Date: {extracted['date']}")
        else:
            print(f"❌ Receipt analysis failed: {result.get('error_message')}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def test_api_endpoint():
    """Test the API endpoint (requires server to be running)."""
    import requests
    
    print("\n🌐 Testing API Endpoint\n")
    print("Make sure the server is running: python -m api.server\n")
    
    test_image_path = Path(__file__).parent.parent / "tests" / "test_receipt.jpg"
    
    if not test_image_path.exists():
        print("⚠️  No test image found at tests/test_receipt.jpg")
        print("Skipping API test...")
        return
    
    try:
        url = "http://localhost:8000/documents/analyze"
        
        with open(test_image_path, "rb") as f:
            files = {"file": (test_image_path.name, f, "image/jpeg")}
            data = {"analysis_type": "receipt"}
            
            print(f"📤 Sending request to {url}...")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API test successful!")
                print(f"Document type: {result.get('document_type')}")
                print(f"Summary: {result.get('summary')}")
                if result.get("extracted_data"):
                    print(f"Extracted data: {result.get('extracted_data')}")
            else:
                print(f"❌ API test failed: {response.status_code}")
                print(response.text)
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Check if google-generativeai is installed
    try:
        import google.generativeai
        import PIL.Image
    except ImportError as e:
        print("❌ Missing dependencies!")
        print(f"Error: {e}")
        print("\nInstall with: pip install google-generativeai pillow")
        sys.exit(1)
    
    # Check API key
    from config.settings import settings
    if not settings.google_api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not set in environment")
        print("Set it in .env file or environment variable")
    
    # Run tests
    test_document_analysis()
    
    # Ask if user wants to test API
    try:
        import requests
        test_api_endpoint()
    except ImportError:
        print("\n💡 Install 'requests' to test API endpoint: pip install requests")

