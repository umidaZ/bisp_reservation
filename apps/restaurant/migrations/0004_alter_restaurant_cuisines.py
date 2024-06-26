# Generated by Django 4.2.10 on 2024-03-21 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0003_alter_restaurant_cuisines'),
    ]

    operations = [
        migrations.AlterField(
            model_name='restaurant',
            name='cuisines',
            field=models.ManyToManyField(default=[1], related_name='restaurants', to='restaurant.cuisine'),
        ),
    ]
