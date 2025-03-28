# Generated by Django 5.1.6 on 2025-03-03 05:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_quotationrequest_resolution'),
    ]

    operations = [
        migrations.CreateModel(
            name='Insurer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='quotationrequest',
            name='on_field',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.RemoveField(
            model_name='quotationrequest',
            name='preferred_insurer',
        ),
        migrations.AddField(
            model_name='quotationrequest',
            name='preferred_insurer',
            field=models.ManyToManyField(related_name='quotation_requests', to='tickets.insurer'),
        ),
    ]
