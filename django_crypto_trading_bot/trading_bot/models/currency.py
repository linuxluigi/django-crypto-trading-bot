from django.db import models


class Currency(models.Model):
    """
    Cryptocurrency
    """

    name = models.CharField(max_length=50, blank=True, null=True)
    short = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return "{0}: {1}".format(self.pk, self.short)
