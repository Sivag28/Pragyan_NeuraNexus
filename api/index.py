"""
Vercel API handler for AI Patient Triage System
This file wraps the Flask app to work with Vercel's serverless functions
"""

import os
import sys

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app

# Disable Flask's debug mode for production
flask_app.debug = False

def handler(request):
    """
    Vercel serverless function handler
    """
    # Get the path and method from the request
    path = request.path if hasattr(request, 'path') else '/'
    method = request.method if hasattr(request, 'method') else 'GET'
    
    # Get query params
    query_string = ''
    if hasattr(request, 'query'):
        query_string = request.query.decode('utf-8')
    
    # Get request body for POST/PUT/PATCH
    json_data = None
    if method in ['POST', 'PUT', 'PATCH']:
        body = request.get_data()
        if body:
            import json
            try:
                json_data = json.loads(body.decode('utf-8'))
            except:
                pass
    
    # Create a fake 'environ' for Flask
    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '',
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '5000',
        'HTTP_HOST': 'localhost:5000',
        'wsgi.url_scheme': 'https',
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
    }
    
    # Handle the request using Flask's WSGI interface
    response = flask_app.full_dispatch_request(flask_app.request_class(environ))
    
    # Return the response
    return response.get_data(), response.status_code, {
        'Content-Type': response.content_type,
        'Set-Cookie': response.headers.get('Set-Cookie', ''),
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
