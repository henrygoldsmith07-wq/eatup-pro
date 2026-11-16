#!/usr/bin/env python3
"""Vercel serverless entry point for the EatUp Pro API."""

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Serverless filesystems are read-only; keep the analytics database in /tmp.
if os.getenv('VERCEL'):
    import data.analytics_db as analytics_db

    analytics_db.DEFAULT_DB_PATH = Path('/tmp') / 'analytics.db'

from api_server import app  # noqa: E402  (must follow the DB path override)


def handler(request):
    """Translate a Vercel request into a Flask test-client call and back."""
    try:
        parsed = urlparse(request.url)
        path = parsed.path or '/'
        headers = dict(getattr(request, 'headers', {}) or {})
        body = request.get_data() if hasattr(request, 'get_data') else b''
        query = parsed.query

        with app.test_client() as client:
            response = client.open(
                path=path,
                method=request.method,
                headers=headers,
                data=body,
                query_string=query,
            )

        return {
            'statusCode': response.status_code,
            'headers': {name: value for name, value in response.headers},
            'body': response.get_data(as_text=True),
        }
    except Exception as exc:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(exc), 'type': type(exc).__name__}),
        }
