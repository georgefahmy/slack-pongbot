# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_on', models.DateTimeField(verbose_name='start_on')),
                ('end_on', models.DateTimeField(null=True, verbose_name='end_on')),
                ('active', models.BooleanField(default=True)),
            ],
        ),
    ]
