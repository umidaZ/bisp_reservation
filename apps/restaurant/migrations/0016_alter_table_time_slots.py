# Generated by Django 4.2.11 on 2024-03-29 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0015_alter_restaurant_cuisines_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='table',
            name='time_slots',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
