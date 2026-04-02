"""
Vercel Serverless Entry Point
Routes all requests to the Flask application.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a WSGI app named 'app'
