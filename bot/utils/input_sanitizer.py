import re
import html
from urllib.parse import urlparse

def sanitize_input(text):
    """Sanitize user input for logging."""
    if not text:
        return ''
    # Remove any PII patterns (emails, IPs, etc.)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', text)
    text = re.sub(r'(password|token|key|secret)=[\S]+', r'\1=[REDACTED]', text)
    return html.escape(text)

def get_safe_domain(url):
    """Extract and normalize domain for logging."""
    try:
        if not url:
            return 'invalid-url'
        parsed = urlparse(url)
        if not parsed.netloc:
            return 'invalid-url'
        # Get base domain without subdomains
        domain_parts = parsed.netloc.split('.')
        if len(domain_parts) > 2:
            return '.'.join(domain_parts[-2:])
        return parsed.netloc
    except:
        return 'invalid-url' 