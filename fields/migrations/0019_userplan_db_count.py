# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-01 01:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fields', '0018_userplan_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='userplan',
            name='db_count',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
