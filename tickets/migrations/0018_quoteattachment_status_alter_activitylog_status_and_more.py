# Generated by Django 5.1.6 on 2025-03-07 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0017_alter_activitylog_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quoteattachment',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], default='Pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='activitylog',
            name='status',
            field=models.CharField(choices=[('Open', 'Open'), ('Assigned', 'Assigned'), ('Resolved', 'Resolved'), ('Incomplete', 'Incomplete'), ('Accepted', 'Accepted')], max_length=20),
        ),
        migrations.AlterField(
            model_name='quotationrequest',
            name='status',
            field=models.CharField(choices=[('Open', 'Open'), ('Assigned', 'Assigned'), ('Resolved', 'Resolved'), ('Incomplete', 'Incomplete'), ('Accepted', 'Accepted')], default='Open', max_length=20),
        ),
    ]
