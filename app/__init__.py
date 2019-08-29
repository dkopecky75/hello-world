"""
Package configuration and Flask appliction intialization for the vocabulary.
"""

# Authors: Dieter Kopecky <dieter.kopecky@boehringer-ingelheim.com>

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from app import models, views
