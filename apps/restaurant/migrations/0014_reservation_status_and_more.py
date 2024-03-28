# Generated by Django 4.2.11 on 2024-03-28 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0013_alter_restaurant_closing_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='status',
            field=models.CharField(blank=True, choices=[('accepted', 'Accepted'), ('rejected', 'Rejected'), ('waiting', 'Waiting')], default='waiting', max_length=8, null=True),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='special_requests',
            field=models.TextField(),
        ),
    ]