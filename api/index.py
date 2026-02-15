"""
Vercel API handler for AI Patient Triage System
This file wraps the Flask app to work with Vercel's serverless functions
"""

import os
import sys

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app

def handler(request):
    """
    Vercel serverless function handler
    """
    # Get the path and method from the request
    path = request.path if hasattr(request, 'path') else '/'
    method = request.method if hasattr(request, 'method') else 'GET'
    
    # Handle the request using Flask's test client
    with flask_app.test_client() as client:
        # Get query params
        query_string = ''
        if hasattr(request, 'query'):
            query_string = request.query.decode('utf-8')
        
        # Make the request
        response = client.open(
            path=path,
            method=method,
            query_string=query_string,
            json=request.get_json(silent=True) if method in ['POST', 'PUT', 'PATCH'] else None
        )
        
        # Return the response
        return response.get_data(), response.status_code, {
            'Content-Type': response.content_type,
            'Set-Cookie': response.headers.get('Set-Cookie', '')
        }
