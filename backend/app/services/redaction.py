import re

class RedactionService:
    """
    Service to redact PII from text messages.
    Currently uses Regex for basic PII (Phone, Email, generic IDs).
    """
    
    # Regex patterns
    PHONE_PATTERN = r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Simple MRN/ID pattern (e.g., #12345 or ID: 12345)
    ID_PATTERN = r'\b(ID|MRN)[:#]?\s*(\d+)\b'

    @staticmethod
    def redact_pii(text: str) -> str:
        """
        Redacts phone numbers, emails, and potential IDs from the text.
        Replaces them with [REDACTED].
        """
        redacted_text = text
        
        # Redact Phone Numbers
        redacted_text = re.sub(RedactionService.PHONE_PATTERN, '[PHONE REDACTED]', redacted_text)
        
        # Redact Emails
        redacted_text = re.sub(RedactionService.EMAIL_PATTERN, '[EMAIL REDACTED]', redacted_text, flags=re.IGNORECASE)
        
        # Redact IDs
        redacted_text = re.sub(RedactionService.ID_PATTERN, r'\1 [ID REDACTED]', redacted_text, flags=re.IGNORECASE)
        
        return redacted_text
