from django.db import models

# Create your models here.


class Game(models.Model):
    moves = models.CharField(null=True)
    computer_think_time_ms = models.PositiveSmallIntegerField(default=1)
