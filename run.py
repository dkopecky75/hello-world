"""
This module is the main entry point into the Flask-based vocabulary application.
Start calling 'env FLASK_APP=run.py /apps/prod/python/python3/bin/flask run'
"""

# Authors: Dieter Kopecky <dieter.kopecky@boehringer-ingelheim.com>

from app import app
app.run(debug=True)