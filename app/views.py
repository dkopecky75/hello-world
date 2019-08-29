"""
This module gathers the web service entry points that are served by the vocabulary.
"""

# Authors: Dieter Kopecky <dieter.kopecky@boehringer-ingelheim.com>

from app import app, db, models

import os
import json
import datetime

from flask import flash, request, redirect
from werkzeug.utils import secure_filename
from sqlalchemy import func, exc

import textract
# from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


def add_service_info_to_json(code, state, json_obj=None):
    """ Adds a service status code and state to a JSON object in order to improve service response readability.
    If no JSON object is handed over, a new service information JSON is created.
    """

    if json_obj is None:
        json_obj = {}

    json_obj['code'] = code
    json_obj['state'] = state
    return json_obj


def allowed_file(filename):
    """ Check whether a filename is valid and the file is in the supported file types.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def getUserAndCatalogue():
    """ Returns the current user and his catalogue. Currently returns the single standard user of the system.
    """
    user = models.User.query.filter_by(userName='kopeckyd').first()
    catalogue = user.catalogue
    return user, catalogue


@app.route("/")
def login():
    """ Placeholder for a future login endpoint
    """
    user, catalogue = getUserAndCatalogue()
    return json.dumps(user.json(), sort_keys=True)


@app.route("/book/find")
def find_books():
    """ Search for books, specifying title, author, language as query parameters. Supports substring searches.
    """
    title = request.args.get('title', '%')
    author = request.args.get('author', '%')
    language = request.args.get('language', '%')

    try:
        books = db.session.query(models.Book).filter(models.Book.title.like(title),
                                                     models.Book.author.like(author),
                                                     models.Book.language.like(language)).all()

        json_obj = add_service_info_to_json(code='OK', state='Found %d books' % len(books))
        book_list = []

        for book in books:
            book_list.append(book.json())

        json_obj['books'] = book_list
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)


@app.route("/book/findtitle/<string:title>")
def find_books_by_title(title):
    """ Search for books by title only, supports only exact searches
    """
    try:
        books = models.Book.query.filter_by(title=title).all()
        json_obj = add_service_info_to_json(code='OK', state='Found %d books' % len(books))
        book_list = []

        for book in books:
            book_list.append(book.json())

        json_obj['books'] = book_list
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)


@app.route("/book/findauthor/<string:author>")
def find_books_by_author(author):
    """ Search for books by author only, supports only exact searches
    """
    try:
        books = models.Book.query.filter_by(author=author).all()
        json_obj = add_service_info_to_json(code='OK', state='Found %d books' % len(books))
        book_list = []

        for book in books:
            book_list.append(book.json())

        json_obj['books'] = book_list
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)


@app.route("/book/add")
def add_book():
    """ Add a book specifying the data as query parameters and returns the newly generated object
    """
    try:
        title = request.args.get('title', None)
        author = request.args.get('author', None)
        language = request.args.get('language', None)

        if title is None or author is None or language is None:
            json_obj = add_service_info_to_json(code='Error', state='Missing parameter(s)')
        else:
            existing = models.Book.query.filter_by(title=title, author=author, language=language).first()
            if existing is None:
                book = models.Book(title=title, author=author, language=language)
                db.session.add(book)
                db.session.commit()
                db.session.refresh(book)
                json_obj = add_service_info_to_json(code='OK', state='Book created successfully',
                                                    json_obj=book.json())
            else:
                json_obj = add_service_info_to_json(code ='OK', state ='Book exists, using existing',
                                                    json_obj=existing.json())
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)


def process_abstract(file_path, min_letters):
    """ A simple text processing approach for this use case, can be extended to deal with links etc quite easily.
    NLTK was also tested but was oversized for this case.
    """
    # Ensure that we are working with str(unicode) to be JSON serializable
    text = textract.process(file_path).decode('utf8')
    tokens = text.split()
    # tokens = word_tokenize(text, 'english')
    punctuations = ['(', ')', ';', ':', '[', ']', ',']
    # stop_words = stopwords.words('english')
    keywords = [word for word in tokens if word not in punctuations and len(word) >= min_letters]
    return keywords


@app.route("/book/<int:book_id>/upload", methods=['GET', 'POST'])
def upload_file(book_id):
    """ A simple GUI-based upload form to simplify testing, which allows to upload the abstract.
    """
    if request.method == 'POST':
        min_letters = int(request.form.get('letters', '3'))
        # check if the post request has the file part

        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)

                user, catalogue = getUserAndCatalogue()
                existing = models.Vocabulary.query.filter_by(catalogueId=catalogue.id, bookId=book_id).first()
                if existing is not None:
                    # Clean up existing vocabulary in case it already exists
                    db.session.delete(existing)
                    db.session.commit()

                # Create a new vocabulary to hold the data
                vocabulary = models.Vocabulary(catalogueId=catalogue.id, bookId=book_id, letterLimit=min_letters)
                db.session.add(vocabulary)
                book = models.Book.query.filter_by(id=book_id).first()

                keywords = process_abstract(path, min_letters)
                os.remove(path)

                for keyword in keywords:
                    word = models.Word.query.filter_by(language=book.language, text=keyword).first()
                    if word is None:
                        word = models.Word(text=keyword, language=book.language)
                        db.session.add(word)
                    usage = models.WordUsage(vocabularyId=vocabulary.id, word=word, creation=datetime.datetime.now())
                    db.session.add(usage)

                db.session.commit()
                db.session.refresh(vocabulary)
                json_obj = add_service_info_to_json(code='OK', state='Vocabulary created successfully',
                                                    json_obj=vocabulary.json())
            except IOError as ioerr:
                json_obj = add_service_info_to_json(code='Error', state=str(ioerr))
            except exc.OperationalError as err:
                json_obj = add_service_info_to_json(code='Error', state=str(err))

            return json.dumps(json_obj, sort_keys=True)

    return app.config['FORM_DATA']


@app.route("/vocabulary/<string:title>")
def get_vocabulary(title):
    """ Search vocabularies by title. If multiple matching books are found, they are returned as separate list items
    """
    try:
        user, catalogue = getUserAndCatalogue()
        vocabularies = models.Vocabulary.query.filter_by(catalogueId=catalogue.id).join(models.Book).\
            filter_by(title=title).all()

        vocabulary_list = []
        for vocabulary in vocabularies:
            vocabulary_list.append(vocabulary.json())

        json_obj = add_service_info_to_json(code='OK', state='Found %d vocabularies' % len(vocabulary_list))
        json_obj['vocabularies'] = vocabulary_list
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)


@app.route("/vocabulary/<string:title>/frequent")
def get_frequent_words(title):
    """ Get the most frequent <n> words for a particular book title.
    """
    return get_words_by_frequency(title, app.config['WORD_COUNT_LIMIT'], True)


@app.route("/vocabulary/<string:title>/infrequent")
def get_infrequent_words(title):
    """ Get the least frequent <n> words for a particular book title.
    """
    return get_words_by_frequency(title, app.config['WORD_COUNT_LIMIT'], False)


def get_words_by_frequency(title, count, descending=True):
    """ Get the least or most frequent <n> words for a particular book title for the current user.
    If multiple matching books are found, they are returned as separate list items
    """

    try:
        user, catalogue = getUserAndCatalogue()
        books = models.Book.query.filter_by(title=title).all()
        book_list = []

        for book in books:
            book_json_obj = book.json()
            hits = models.WordUsage.query.join(models.Vocabulary).\
                filter_by(catalogueId=catalogue.id,bookId=book.id).join(models.Word).join(models.Book).\
                with_entities(models.Book.title, models.Book.author, models.Book.language, models.Word.text,
                                  func.count(models.Word.text).label('total')).\
                group_by(models.Book.title, models.Book.author, models.Book.language, models.Word.text). \
                order_by('total DESC' if descending else 'total ASC' + ', text ASC').\
                limit(count).all()

            book_json_obj['words'] = hits
            book_list.append(book_json_obj)

        json_obj = add_service_info_to_json(code='OK', state='OK')
        json_obj['books'] = book_list
    except exc.OperationalError as err:
        json_obj = add_service_info_to_json(code='Error', state=str(err))

    return json.dumps(json_obj, sort_keys=True)