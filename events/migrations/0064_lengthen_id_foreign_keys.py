# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-01 11:25
# Manual migration is needed due to Django bug https://code.djangoproject.com/ticket/25012
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0063_lengthen_origin_id_and_id_fields'),
    ]

    operations = [
        migrations.RunSQL('ALTER TABLE events_openinghoursspecification ALTER place_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_place_divisions ALTER place_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_keyword_alt_labels ALTER keyword_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_keywords ALTER keyword_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_audience ALTER keyword_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_keywordset_keywords ALTER keyword_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_keywordset_keywords ALTER keywordset_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_keywords ALTER event_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_in_language ALTER event_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_audience ALTER event_id TYPE varchar(100);'),
        migrations.RunSQL('ALTER TABLE events_event_images ALTER event_id TYPE varchar(100);'),

    ]