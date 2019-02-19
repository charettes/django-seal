# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-19 16:03
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [('contenttypes', '0002_remove_content_type_name')]

    operations = [
        migrations.CreateModel(
            name='Climate',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('temperature', models.IntegerField()),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Leak',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                (
                    'climates',
                    models.ManyToManyField(
                        blank=True, related_name='locations', to='tests.Climate'
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Nickname',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=24)),
                ('object_id', models.PositiveIntegerField()),
                (
                    'content_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to='contenttypes.ContentType',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='SeaGull',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                )
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='SeaLion',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('height', models.PositiveIntegerField()),
                ('weight', models.PositiveIntegerField()),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='GreatSeaLion',
            fields=[
                (
                    'sealion_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='tests.SeaLion',
                    ),
                )
            ],
            options={'abstract': False},
            bases=('tests.sealion',),
        ),
        migrations.AddField(
            model_name='sealion',
            name='leak',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sealion_just_friends',
                to='tests.Leak',
            ),
        ),
        migrations.AddField(
            model_name='sealion',
            name='leak_o2o',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sealion_soulmate',
                to='tests.Leak',
            ),
        ),
        migrations.AddField(
            model_name='sealion',
            name='location',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='visitors',
                to='tests.Location',
            ),
        ),
        migrations.AddField(
            model_name='sealion',
            name='previous_locations',
            field=models.ManyToManyField(
                related_name='previous_visitors', to='tests.Location'
            ),
        ),
        migrations.AddField(
            model_name='seagull',
            name='sealion',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gull',
                to='tests.SeaLion',
            ),
        ),
        migrations.CreateModel(
            name='SealionProxy',
            fields=[],
            options={'proxy': True, 'indexes': []},
            bases=('tests.sealion',),
        ),
    ]
