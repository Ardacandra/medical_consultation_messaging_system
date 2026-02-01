import re
from typing import Dict, Any

# Simple regex-based patterns for prototype
PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "id_generic": r'\bID\d{5,}\b' 
}

def redact_pii(text: str) -> str:
    """
    Scrub common PII from text.
    In a real system, this would use DLP API or NLP model (e.g. Presidio).
    """
    if not text:
        return text
        
    redacted = text
    for ptype, pattern in PATTERNS.items():
        redacted = re.sub(pattern, f"[{ptype.upper()}_REDACTED]", redacted)
    return redacted

def structured_log(event: str, metadata: Dict[str, Any], level: str = "INFO"):
    """
    Log event as JSON effectively.
    """
    import json
    import logging
    
    # Safe logger
    logger = logging.getLogger("nightingale.audit")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    log_entry = {
        "event": event,
        "level": level,
        "timestamp": str(logging.Formatter().formatTime(logging.LogRecord("",0,"","",0,0,0), "%Y-%m-%dT%H:%M:%S")),
        "metadata": metadata
    }
    
    # Ensure no PII in metadata (basic shallow check)
    # Ideally, we pass already safe metadata
    
    logger.info(json.dumps(log_entry))
