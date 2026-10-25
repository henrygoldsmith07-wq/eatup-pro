#!/usr/bin/env python3
"""
EatUp Pro v8.2 - Vercel Serverless API Handler
Handles all API requests via HTTP functions
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server import app


# Vercel expects this handler
def handler(request):
    """Handle HTTP requests from Vercel"""
    
    # CORS preflight handling
    if request.method == 'OPTIONS':
        return handle_cors_preflight(request)
    
    # Route API requests
    if request.url.startswith('/api/'):
        return call_flask_app(request)
    
    # Serve static files
    return serve_static_file(request)


def handle_cors_preflight(request):
    """Handle CORS preflight requests"""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
    }
    
    return {
        "statusCode": 200,
        "headers": headers,
        "body": ""
    }


def call_flask_app(request):
    """Forward request to Flask app"""
    try:
        # Create WSGI environment
        from werkzeug.test import EnvironBuilder
        from werkzeug.wrappers import Response
        
        # Parse request data
        method = request.method
        url = request.url
        headers = dict(request.headers)
        
        # Get query params
        query_string = request.query_string.decode() if hasattr(request, 'query_string') else ''
        
        # Build WSGI environ
        builder = EnvironBuilder(
            method=method,
            path=url.replace('https://your-domain.vercel.app/api/', ''),
            query_string=query_string.encode(),
            headers=headers,
            data=request.get_data() if hasattr(request, 'get_data') else b'',
            base_url=url
        )
        
        env = builder.get_wsgi_env()
        
        # Call Flask with WSGI environ
        response = app(env, lambda status, headers: None)
        
        # Convert Flask response to Vercel format
        vercel_response = {
            "statusCode": response.status_code,
            "headers": {k: v for k, v in response.headers},
            "body": response.get_data(as_text=True)
        }
        
        # Add CORS headers
        vercel_response["headers"]["Access-Control-Allow-Origin"] = "*"
        
        return vercel_response
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e), "type": type(e).__name__})
        }


def serve_static_file(request):
    """Serve static files (HTML, CSS, JS, etc.)"""
    static_path = request.url.split('/api/')[0]
    
    # Check if file exists
    index_html = Path("index.html")
    
    if request.url.endswith('/') or request.url.endswith('.html'):
        if index_html.exists():
            content_type = "text/html; charset=utf-8"
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": content_type,
                    "Cache-Control": "public, max-age=3600"
                },
                "body": index_html.read_text()
            }
    
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "File not found"})
    }
