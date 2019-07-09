# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_season'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rankings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.CharField(max_length=200)),
                ('ranking', models.IntegerField(default=1000)),
                ('created_on', models.DateTimeField('created_on')),
            ],
        ),
    ]
