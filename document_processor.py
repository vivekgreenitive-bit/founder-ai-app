import os
import pdfplumber
import pandas as pd
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

def extract_text_from_file(file_path: str) -> str:
    """Extracts text from various file formats."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
            
    elif ext == ".pdf":
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
        
    elif ext in [".csv", ".xls", ".xlsx"]:
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            # Convert dataframe to a readable string format for the LLM
            return df.to_string()
        except Exception as e:
            return f"Error parsing spreadsheet: {str(e)}"
            
    elif ext in [".png", ".jpg", ".jpeg"]:
        if pytesseract is None:
            return "Image extraction is currently disabled (pytesseract compatibility issue with Python 3.14)."
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            return f"Error extracting text from image: {str(e)}"
            
    else:
        text = f"Unsupported file format: {ext}"

    return sanitize_extracted_text(text)

def sanitize_extracted_text(raw_text: str) -> str:
    """
    Sanitizes extracted document text to strip common indirect prompt injection attacks, 
    system prompt overrides, and unauthorized control tags before passing to LLM context.
    """
    import re
    if not raw_text:
        return ""

    # Neutralize common prompt injection system override patterns
    injection_patterns = [
        r"(?i)ignore\s+(previous|all)\s+(instructions|prompts|rules)",
        r"(?i)system\s*:\s*",
        r"(?i)\[system\s+instruction\]",
        r"(?i)override\s+policy",
        r"(?i)transfer\s+all\s+funds",
        r"(?i)delete\s+(all\s+)?database"
    ]

    sanitized = raw_text
    for pattern in injection_patterns:
        sanitized = re.sub(pattern, "[FILTERED_SECURITY_VIOLATION]", sanitized)

    return sanitized

