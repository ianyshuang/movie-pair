from django.db import models
from mongoengine import *


# Create your models here.
class TopMovie(Document):
  name = StringField(max_length = 100)
  week_revenue = IntField(default = 0)


class Movie(Document):
  name = StringField(max_length = 200, required = True)
  category = ListField(max_length = 10, required = True)
  release_date = StringField(max_length = 10, required = True)
  length = StringField(max_length = 10, required = True)
  imdb_score = FloatField()
  description = StringField(max_length = 1000)
  image_url = StringField()

  def get_all(self):
    return {'name': self.name, 'category': self.category, 'release_date': self.release_date, 'length': length, 'imdb_score': imdb_score, 'description': description, 'image_url': image_url}