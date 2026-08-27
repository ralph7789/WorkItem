import logging
from typing import Optional
import keyring
import bleach

logger = logging.getLogger(__name__)

# Constants for keyring storage
SERVICE_NAME = "workitems_app_github"
USERNAME = "workitems_user"

import os
import json
from pathlib import Path

FALLBACK_TOKEN_FILE = Path.home() / '.workitems' / 'token.json'

def _save_fallback(token: str):
    FALLBACK_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FALLBACK_TOKEN_FILE, 'w') as f:
        json.dump({"token": token}, f)

def _get_fallback() -> Optional[str]:
    if FALLBACK_TOKEN_FILE.exists():
        try:
            with open(FALLBACK_TOKEN_FILE, 'r') as f:
                return json.load(f).get("token")
        except:
            return None
    return None

def save_github_token(token: str) -> None:
    """
    Save the GitHub PAT securely using the OS keyring, with a fallback.
    """
    if not token:
        raise ValueError("Token cannot be empty")
        
    try:
        keyring.set_password(SERVICE_NAME, USERNAME, token)
        logger.info("GitHub token successfully stored in OS keyring.")
    except Exception as e:
        logger.warning(f"Keyring failed, falling back to local file storage: {e}")
        _save_fallback(token)

def get_github_token() -> Optional[str]:
    """
    Retrieve the GitHub PAT securely from the OS keyring, or fallback.
    """
    try:
        token = keyring.get_password(SERVICE_NAME, USERNAME)
        if token:
            return token
    except Exception as e:
        logger.warning(f"Keyring retrieve failed: {e}")
        
    # Attempt fallback
    return _get_fallback()

def sanitize_html(raw_html: str) -> str:
    """
    Sanitize untrusted HTML to prevent XSS attacks using bleach.
    Allows only a safe subset of tags and attributes necessary for Markdown.
    """
    if not raw_html:
        return ""
        
    # Standard safe tags for rendering GitHub issues/comments
    allowed_tags = {
        'p', 'div', 'span', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'pre', 'code',
        'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li', 'a', 'img', 'blockquote'
    }
    
    allowed_attributes = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'rel'],
        'img': ['src', 'alt', 'title']
    }
    
    # Restrict allowed protocols to prevent javascript: or data: URIs
    allowed_protocols = ['http', 'https', 'mailto']

    sanitized = bleach.clean(
        raw_html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True  # Strip disallowed tags entirely rather than escaping them
    )
    
    return sanitized
