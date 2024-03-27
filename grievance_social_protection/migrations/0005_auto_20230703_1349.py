# Generated by Django 3.2.20 on 2023-07-03 13:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('grievance_social_protection', '0004_auto_20230425_1638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='event_location',
        ),
        migrations.RemoveField(
            model_name='ticket',
            name='insuree_location',
        ),
        migrations.AlterField(
            model_name='ticket',
            name='phone',
            field=models.CharField(blank=True, db_column='PhoneNumber', max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ticket_code',
            field=models.CharField(blank=True, db_column='TicketCode', max_length=16, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ticket_priority',
            field=models.CharField(blank=True, db_column='TicketPriority', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ticket_status',
            field=models.CharField(blank=True, db_column='TicketStatus', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='ticketattachment',
            name='ticket',
            field=models.ForeignKey(blank=True, db_column='TicketId', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='attachment', to='grievance.ticket'),
        ),
    ]
