"""Document Analysis Tool for Customer Support"""
import os
import base64
import logging
from typing import Dict, Optional, Any
from io import BytesIO

try:
    import google.generativeai as genai
    import PIL.Image
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI or PIL not available. Install with: pip install google-generativeai pillow")

from config.settings import settings

logger = logging.getLogger(__name__)

# Set API key
os.environ["GOOGLE_API_KEY"] = settings.google_api_key


def analyze_document(
    file_data: bytes,
    file_type: str,
    analysis_type: str = "auto",
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a document (PDF or image) using Gemini Vision API.
    
    Args:
        file_data: Binary file data (PDF or image bytes)
        file_type: MIME type (e.g., "application/pdf", "image/jpeg", "image/png")
        analysis_type: Type of analysis to perform:
            - "auto": Automatically detect document type and extract relevant info
            - "receipt": Extract order/receipt information (order number, amount, date, items)
            - "invoice": Extract invoice information
            - "product_photo": Analyze product photo for defects/issues
            - "order_confirmation": Extract order confirmation details
            - "general": General text extraction and summary
        context: Optional context about what to look for (e.g., "Find the order number")
    
    Returns:
        Dictionary with analysis results:
        {
            "status": "success" | "error",
            "document_type": "receipt" | "invoice" | "product_photo" | "unknown",
            "extracted_data": {
                "order_id": "...",
                "amount": 99.99,
                "date": "2024-01-15",
                "items": [...],
                ...
            },
            "text_content": "Full extracted text",
            "summary": "Brief summary of document",
            "confidence": 0.95,
            "error_message": "..." (if error)
        }
    """
    if not GEMINI_AVAILABLE:
        return {
            "status": "error",
            "error_message": "Gemini API not available. Please install google-generativeai and pillow packages."
        }
    
    try:
        # Convert file to base64
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # Build prompt based on analysis type
        prompt = _build_analysis_prompt(analysis_type, context)
        
        # Use Google Generative AI (simpler API)
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
        except ImportError:
            return {
                "status": "error",
                "error_message": "Google Generative AI library not available. Install with: pip install google-generativeai"
            }
        
        # Prepare content for Gemini
        # Gemini Vision API supports images directly
        if file_type.startswith("image/"):
            # For images, use PIL Image
            import PIL.Image
            from io import BytesIO
            
            try:
                image = PIL.Image.open(BytesIO(file_data))
                model = genai.GenerativeModel("gemini-2.5-flash-lite")
                
                # Configure generation for better JSON output
                generation_config = {
                    "temperature": 0.1,  # Low temperature for accuracy
                    "max_output_tokens": 2048,
                }
                
                response = model.generate_content(
                    [prompt, image],
                    generation_config=generation_config
                )
                response_text = response.text
                logger.info(f"Gemini response (first 500 chars): {response_text[:500]}")
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                return {
                    "status": "error",
                    "error_message": f"Failed to process image: {str(e)}"
                }
        elif file_type == "application/pdf":
            # For PDFs, we need to convert to images first
            # For now, return error suggesting to convert PDF to image
            # In production, you could use pdf2image library
            return {
                "status": "error",
                "error_message": "PDF support requires conversion to images. Please convert PDF to image (JPG/PNG) or install pdf2image library for automatic conversion."
            }
        else:
            return {
                "status": "error",
                "error_message": f"Unsupported file type: {file_type}. Supported: JPG, PNG, WebP (PDF support requires pdf2image library)"
            }
        
        # Extract structured data from response
        extracted_data = _parse_analysis_response(response_text, analysis_type)
        
        return {
            "status": "success",
            "document_type": _detect_document_type(response_text, analysis_type),
            "extracted_data": extracted_data,
            "text_content": response_text,
            "summary": _generate_summary(response_text, extracted_data),
            "confidence": 0.9  # Gemini Vision is generally very accurate
        }
        
    except Exception as e:
        logger.error(f"Error analyzing document: {e}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"Failed to analyze document: {str(e)}"
        }


def _build_analysis_prompt(analysis_type: str, context: Optional[str] = None) -> str:
    """Build the analysis prompt based on document type."""
    
    base_prompt = "Analyze this document and extract relevant information. "
    
    if analysis_type == "receipt" or analysis_type == "auto":
        prompt = base_prompt + """
        IMPORTANT: Analyze the IMAGE CONTENT, not the filename. Ignore any filename information.
        
        Extract the following information from this receipt/invoice/order confirmation IMAGE:
        1. Order number or order ID (look for patterns like "Order #", "Order ID", "Order Number", standalone numbers like 12345, ORDER-123)
           - DO NOT extract numbers from dates or timestamps
           - Order IDs are typically 5-10 digits, standalone (not part of dates)
        2. Total amount (look for "Total", "Amount", "$", currency symbols)
        3. Date (order date, purchase date, transaction date) - format as YYYY-MM-DD
        4. Items/products purchased (names, quantities, prices)
        5. Customer information if visible (name, email, customer ID)
        6. Store/merchant name
        
        You MUST respond with ONLY valid JSON, no other text. Format:
        {
            "order_id": "extracted order number or null",
            "amount": numeric amount or null,
            "date": "YYYY-MM-DD format or null",
            "items": [{"name": "...", "quantity": 1, "price": 0.0}],
            "customer_name": "name or null",
            "merchant": "store name or null"
        }
        
        CRITICAL RULES:
        - Only extract information you can CLEARLY SEE in the image
        - If order_id is not visible, return null (do not guess or extract from dates/filenames)
        - Order IDs are typically 5-10 digits, standalone numbers
        - Do NOT extract dates or timestamps as order IDs
        - If you cannot find a field, use null
        - Return ONLY the JSON object, no explanations
        """
    elif analysis_type == "invoice":
        prompt = base_prompt + """
        Extract invoice information:
        1. Invoice number
        2. Invoice date
        3. Due date
        4. Total amount
        5. Line items
        6. Customer details
        """
    elif analysis_type == "product_photo":
        prompt = base_prompt + """
        Analyze this product photo and describe:
        1. What product is shown
        2. Any visible defects, damage, or issues
        3. Product condition (new, used, damaged, etc.)
        4. Any text visible on the product or packaging
        5. Overall assessment
        
        Format as JSON:
        {
            "product_description": "...",
            "defects": ["list of issues"],
            "condition": "new|used|damaged|defective",
            "visible_text": "...",
            "assessment": "..."
        }
        """
    elif analysis_type == "order_confirmation":
        prompt = base_prompt + """
        Extract order confirmation details:
        1. Order number
        2. Order date
        3. Items ordered
        4. Shipping address (if visible)
        5. Total amount
        6. Expected delivery date
        """
    else:  # general
        prompt = base_prompt + """
        Extract all text and key information from this document.
        Provide a summary of the document content.
        """
    
    if context:
        prompt += f"\n\nAdditional context: {context}"
    
    return prompt


def _parse_analysis_response(response_text: str, analysis_type: str) -> Dict[str, Any]:
    """Parse the Gemini response and extract structured data."""
    import json
    import re
    
    logger.info(f"Parsing Gemini response: {response_text[:200]}...")
    
    # Try to extract JSON from response (look for JSON block)
    # First try to find JSON wrapped in code blocks
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_block_match:
        try:
            extracted = json.loads(json_block_match.group(1))
            logger.info(f"Extracted JSON from code block: {extracted}")
            return extracted
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object directly
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
    if json_match:
        try:
            extracted = json.loads(json_match.group())
            logger.info(f"Extracted JSON: {extracted}")
            return extracted
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {json_match.group()[:100]}")
    
    # Fallback: extract key information using regex (but be more careful)
    extracted = {}
    
    # Try to find order ID - but be careful not to extract dates or small numbers
    # Order IDs are typically 5-10 digits, standalone
    order_id_patterns = [
        r'(?:order|order\s*#|order\s*id|order\s*number)[:\s#]*([A-Z0-9-]{5,20})',  # Explicit order references
        r'#\s*(\d{5,10})(?![0-9])',  # Standalone # followed by 5-10 digits
        r'(?:order|id)[:\s]+([A-Z0-9-]{5,20})(?=\s|$|,|\.)',  # Order/ID label followed by ID
    ]
    for pattern in order_id_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            potential_id = match.group(1).strip()
            # Validate: should be 5-10 digits or alphanumeric, not a date
            if len(potential_id) >= 5 and len(potential_id) <= 20:
                # Don't extract if it looks like a date (YYYY-MM-DD or similar)
                if not re.match(r'^\d{4}[-/]\d{2}', potential_id):
                    extracted["order_id"] = potential_id
                    logger.info(f"Extracted order_id via regex: {potential_id}")
                    break
    
    # Try to find amount (look for currency symbols or "total")
    amount_patterns = [
        r'(?:total|amount)[:\s]*\$?\s*(\d+\.?\d*)',
        r'\$\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*(?:USD|dollars?)',
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            try:
                amount = float(match.group(1))
                if amount > 0:  # Reasonable amount
                    extracted["amount"] = amount
                    logger.info(f"Extracted amount: {amount}")
                    break
            except ValueError:
                pass
    
    # Try to find date (YYYY-MM-DD format)
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', response_text)
    if date_match:
        date_str = date_match.group(1).replace('/', '-')
        extracted["date"] = date_str
        logger.info(f"Extracted date: {date_str}")
    
    if extracted:
        logger.info(f"Final extracted data: {extracted}")
        return extracted
    else:
        logger.warning("No data extracted, returning raw text")
        return {"raw_text": response_text, "analysis": response_text}


def _detect_document_type(response_text: str, analysis_type: str) -> str:
    """Detect the type of document from the analysis."""
    if analysis_type != "auto":
        return analysis_type
    
    text_lower = response_text.lower()
    
    if any(word in text_lower for word in ["order", "receipt", "purchase", "transaction"]):
        return "receipt"
    elif any(word in text_lower for word in ["invoice", "bill"]):
        return "invoice"
    elif any(word in text_lower for word in ["product", "item", "defect", "damage"]):
        return "product_photo"
    else:
        return "unknown"


def _generate_summary(response_text: str, extracted_data: Dict[str, Any]) -> str:
    """Generate a brief summary of the document analysis."""
    summary_parts = []
    
    if "order_id" in extracted_data and extracted_data["order_id"]:
        summary_parts.append(f"Order ID: {extracted_data['order_id']}")
    
    if "amount" in extracted_data and extracted_data["amount"]:
        summary_parts.append(f"Amount: ${extracted_data['amount']:.2f}")
    
    if "date" in extracted_data and extracted_data["date"]:
        summary_parts.append(f"Date: {extracted_data['date']}")
    
    if summary_parts:
        return " | ".join(summary_parts)
    else:
        return "Document analyzed. See extracted_data for details."


def analyze_receipt_for_order(file_data: bytes, file_type: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a receipt/invoice and extract order information.
    
    Args:
        file_data: Binary file data
        file_type: MIME type
    
    Returns:
        Dictionary with order information extracted from receipt
    """
    return analyze_document(file_data, file_type, analysis_type="receipt")


def analyze_product_photo(file_data: bytes, file_type: str) -> Dict[str, Any]:
    """
    Convenience function to analyze a product photo for defects/issues.
    
    Args:
        file_data: Binary file data
        file_type: MIME type
    
    Returns:
        Dictionary with product analysis results
    """
    return analyze_document(file_data, file_type, analysis_type="product_photo")

