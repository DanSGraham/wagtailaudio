# Generated by Django 2.1.4 on 2018-12-27 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailaudio', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='audio',
            name='thumbnail',
            field=models.FileField(blank=True, upload_to='media_thumbnails', verbose_name='thumbnail'),
        ),
    ]
