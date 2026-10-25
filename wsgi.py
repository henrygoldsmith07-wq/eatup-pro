#!/usr/bin/env python3
"""
EatUp Pro - Production-ready WSGI handler for Vercel/CloudFlare/etc.
"""

from api_server import app as application

# This is needed for WSGI servers (Vercel, gunicorn, waitress, etc.)
application.secret_key = 'eatup-pro-secret-key-2026'
