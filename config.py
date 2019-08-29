"""
This module collects the application wide definitions and constants.
"""

# Authors: Dieter Kopecky <dieter.kopecky@boehringer-ingelheim.com>

import os
basedir = os.path.abspath(os.path.dirname(__file__))

# The database resource, currently SQLite based
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'vocabulaire.db')
# The directory for repository migrations
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Upload folder for books to be parsed, just a temporary store, since the files are removed immediately
UPLOAD_FOLDER = os.path.join(basedir, 'upload')
# File types currently supported by the vocabulary
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Number of hits to return for frequent and infrequent words
WORD_COUNT_LIMIT = 10

FORM_DATA = '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
    <input type=file name=file>
    Letter Limit: <input type=number name=letters min="3" value="3">
    <input type=submit value=Upload>
    </form>'''