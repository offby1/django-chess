import uuid

from django.db import models

# Create your models here.


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moves = models.CharField(null=True)
    computer_think_time_ms = models.PositiveSmallIntegerField(default=1)
