from django.db import models

# Create your models here.


class Game(models.Model):
    moves = models.CharField(null=True)
