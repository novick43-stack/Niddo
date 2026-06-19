"""
Vercel serverless entry-point.
Imports the Flask `app` object from the root-level app.py so that
Vercel can use it as a WSGI handler.
"""
import sys
import os

# Add project root to Python path so `app` module can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

# Vercel expects the WSGI app to be accessible as `app`
# (the variable name matches the @vercel/python convention)
