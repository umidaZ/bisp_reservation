# Generated by Django 4.2.11 on 2024-03-29 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0016_alter_table_time_slots'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='special_requests',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='table',
            name='time_slots',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]