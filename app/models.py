"""
This module gathers all classes forming the data model of the vocabulary. SQLAlchemy is used as ORM to map to the
underlying DB, currently SQLite.
"""

# Authors: Dieter Kopecky <dieter.kopecky@boehringer-ingelheim.com>


from app import db


class User(db.Model):
    """ Return a web service appropriate JSON representation"""
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    userName = db.Column(db.String(12), index=True, unique=True, nullable=False)
    firstName = db.Column(db.String(30), unique=False, nullable=False)
    lastName = db.Column(db.String(30), unique=False, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    catalogue = db.relationship('Catalogue', backref='user', lazy=True, uselist=False)

    def json(self):
        """ Return a web service appropriate JSON representation"""
        obj = self.__dict__.copy()
        obj.pop('_sa_instance_state')
        obj.pop('catalogue')
        return obj

    def __repr__(self):
        return '<User %r>' % (self.userName)

    def __str__(self):
        return 'User %s, %s %s' % (self.userName, self.firstName, self.lastName)


class Catalogue(db.Model):
    """ Class for the collection of vocabularies for a particular user. Could have been skipped for the current
     requirements, but was kept in order to allow for further extensions.
    """

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=False)
    creation = db.Column(db.DateTime, unique=False, nullable=False)
    vocabularies = db.relationship('Vocabulary', backref='catalogue', lazy=True)

    def __repr__(self):
        return '<Catalogue of User %r>' % (self.user.userName)

    def __str__(self):
        return 'Catalogue of User %s, holding %d vocabularies' % (self.user.userName, len(self.vocabularies))


class Book(db.Model):
    """ Class for storing books in the vocabulary. Books are unique across the whole application.
    """

    __table_args__ = (
        db.UniqueConstraint('title', 'author', 'language', name='unique_book_identification'),
    )
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(100), unique=False, nullable=False, index=True)
    author = db.Column(db.String(200), unique=False, nullable=False)
    language = db.Column(db.String(2), unique=False, nullable=False)
    vocabularies = db.relationship('Vocabulary', backref='book', lazy=True)

    def json(self):
        """ Return a web service appropriate JSON representation"""
        obj = self.__dict__.copy()
        obj.pop('_sa_instance_state')
        return obj

    def __repr__(self):
        return '<Book %s %s %s>' % (self.title, self.author, self.language)

    def __str__(self):
        return 'Book %s, %s, %s' % (self.title, self.author, self.language)


class Vocabulary(db.Model):
    """ Class for storing a particular vocabulary. The vocabulary is referencing the book in order to allow
    for a normalised data model and holds a letterLimit attribute to define the minimum world length taken into account.
    """

    __table_args__ = (
        db.UniqueConstraint('catalogueId', 'bookId', name='unique_vocabulary_assignment'),
    )
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    catalogueId = db.Column(db.Integer, db.ForeignKey('catalogue.id'), nullable=False)
    bookId = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    letterLimit = db.Column(db.Integer, primary_key=False, nullable=False)
    words = db.relationship('WordUsage', backref='vocabulary', lazy=True)

    def json(self):
        """ Return a web service appropriate JSON representation"""
        obj = self.__dict__.copy()
        obj.pop('_sa_instance_state')
        wordsJson = []
        for word in self.words:
            wordsJson.append(word.json())
        obj['words'] = wordsJson
        return obj

    def __repr__(self):
        return '<Vocabulary %s %s>' % (self.catalogue.user.userName, self.book.title)

    def __str__(self):
        return 'Vocabulary of User %s and Book %s, holding %d words' % (
            self.catalogue.user.userName, self.book.title, len(self.words))


class Word(db.Model):
    """ Class for storing language specific words. Words are unique across vocabularies, catalogues, and users. The
    assumption of uniqueness across users was added to the original requirements to support multi-user systems.
    """

    __table_args__ = (
        db.UniqueConstraint('text', 'language', name='unique_word_definition'),
    )
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False, index=True)
    language = db.Column(db.String(2), unique=False, nullable=False)
    usages = db.relationship('WordUsage', backref='word', lazy=True)

    def json(self):
        """ Return a web service appropriate JSON representation"""
        obj = self.__dict__.copy()
        obj.pop('_sa_instance_state')
        return obj

    def __repr__(self):
        return '<Word %r %r>' % (self.text, self.language)

    def __str__(self):
        return 'Word "%s" in language %s' % (self.text, self.language)


class WordUsage(db.Model):
    """ Class for storing usage of particular words in a book. Actually the vocabulary is referenced in order to allow
    for a normalised data model. An item is used for every occurrence of a word in a book, in order to allow for storing
    page references in the future.
    """

    id = db.Column(db.Integer, primary_key=True)
    vocabularyId = db.Column(db.Integer, db.ForeignKey('vocabulary.id'))
    wordId = db.Column(db.Integer, db.ForeignKey('word.id'))
    creation = db.Column(db.DateTime, unique=False, nullable=False)
    # pageRef = db.Column(db.Integer, unique=False, nullable=False)

    """ Return a web service appropriate JSON representation"""
    def json(self):
        obj = self.word.json()
        obj['creation'] = str(self.creation)
        return obj
