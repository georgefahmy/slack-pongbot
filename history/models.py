from __future__ import unicode_literals

from django.db import models


class Game(models.Model):
    winner = models.CharField(max_length=200)
    loser = models.CharField(max_length=200)
    created_on = models.DateTimeField('created_on')
    modified_on = models.DateTimeField('modified_on')

    def __str__(self):
        return '{} beat {}'.format(self.winner, self.loser, self.created_on.strftime('%T, %d %b %Y'))

class Season(models.Model):
    start_on = models.DateTimeField('start_on')
    season_number = models.IntegerField(default=1)
    end_on = models.DateTimeField('end_on', null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        if self.end_on is None:
            return "Season {} (started on {} )".format(self.season_number, self.start_on.strftime('%Y/%m/%d'))
        else:
            return "Season {} (started on {}, ended on {} )".format(self.season_number, self.start_on.strftime('%Y/%m/%d'), self.end_on.strftime('%Y/%m/%d'))

class Rankings(models.Model):
    user = models.CharField(max_length=200)
    ranking = models.IntegerField(default=1000)
    created_on = models.DateTimeField('created_on')
