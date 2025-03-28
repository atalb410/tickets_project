# Generated by Django 5.1.6 on 2025-03-06 06:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0013_quotationrequest_comments'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Open', 'Open'), ('Assigned', 'Assigned'), ('Resolved', 'Resolved'), ('Incomplete', 'Incomplete')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=100)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='tickets.quotationrequest')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
