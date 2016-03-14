# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import bulbs.reading_list.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0007_content_evergreen'),
        ('testcontent', '0003_testcontentobj_campaign'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestReadingListObj',
            fields=[
                ('content_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='content.Content')),
                ('foo', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('content.content', bulbs.reading_list.mixins.ReadingListMixin),
        ),
    ]
