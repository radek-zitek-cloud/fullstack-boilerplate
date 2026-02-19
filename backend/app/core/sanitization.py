"""Input sanitization utilities."""

import bleach


def sanitize_html(text: str | None) -> str | None:
    """Sanitize HTML content to prevent XSS attacks.
    
    Removes all HTML tags and returns plain text.
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        Sanitized plain text or None if input was None
    """
    if text is None:
        return None
    
    # Remove all HTML tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    return cleaned


def sanitize_text(text: str | None, max_length: int = 5000) -> str | None:
    """Sanitize plain text input.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text or None if input was None
    """
    if text is None:
        return None
    
    # Strip whitespace and limit length
    cleaned = text.strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned
