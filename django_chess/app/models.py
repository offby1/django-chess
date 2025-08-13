from django.db import models

# Create your models here.

class Game(models.Model):

    board_fen = models.CharField(max_length=200)
