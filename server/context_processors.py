# server/context_processors.py
"""
Context processors globali pentru toate template-urile.
"""
from fastapi import Request
from middleware.csrf import get_csrf_token, csrf_input_tag, csrf_meta_tag


def global_context_processor(request: Request) -> dict:
    """Context global pentru toate template-urile."""
    return {
        "csrf_token": get_csrf_token(request),
        "csrf_input": csrf_input_tag(request),
        "csrf_meta": csrf_meta_tag(request),
    }