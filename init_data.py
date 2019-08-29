#!/apps/prod/python/python3/bin/python

from app import models
from app import db
import datetime

u = models.User(userName = 'kopeckyd',
                firstName = 'Dieter',
                lastName = 'Kopecky',
                email = 'dieter.kopecky@boehringer-ingelheim.com')

db.session.add(u)

c = models.Catalogue(userId=1, creation=datetime.datetime.now())
db.session.add(c)

db.session.commit()
