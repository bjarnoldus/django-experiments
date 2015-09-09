# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enrollment_date', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(null=True)),
                ('alternative', models.CharField(max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('name', models.CharField(serialize=False, primary_key=True, max_length=128)),
                ('description', models.TextField(null=True, blank=True, default='')),
                ('alternatives', jsonfield.fields.JSONField(blank=True, default={})),
                ('relevant_chi2_goals', models.TextField(null=True, blank=True, default='')),
                ('relevant_mwu_goals', models.TextField(null=True, blank=True, default='')),
                ('state', models.IntegerField(choices=[(0, 'Default/Control'), (1, 'Enabled'), (3, 'Track')], default=0)),
                ('start_date', models.DateTimeField(null=True, blank=True, default=datetime.datetime.now, db_index=True)),
                ('end_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='experiment',
            field=models.ForeignKey(to='experiments.Experiment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='enrollment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='enrollment',
            unique_together=set([('user', 'experiment')]),
        ),
    ]
