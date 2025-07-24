# models/blog/__init__.py
"""
Blog module pentru PCE-start Foundation.

Acest modul conține modelele pentru sistemul de blog:
- Post: Articole blog create de Staff
- PostImage: Imagini asociate postărilor (max 5 per post)

Postările sunt create și gestionate exclusiv de Staff cu roluri
super_admin sau manager. Clienții sunt notificați automat despre
postări noi prin Telegram și Email.
"""

from .post import Post
from .post_image import PostImage

__all__ = [
    'Post',
    'PostImage',
]