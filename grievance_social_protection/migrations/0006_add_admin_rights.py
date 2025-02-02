# Generated by Django 3.2.16 on 2023-07-07 13:38

import core.fields
import datetime
from django.db import migrations, models

from core.utils import insert_role_right_for_system


def add_rights(apps, schema_editor):

    insert_role_right_for_system(64, 123000, apps)  # search
    insert_role_right_for_system(64, 123001, apps)  # create
    insert_role_right_for_system(64, 123002, apps)  # update
    insert_role_right_for_system(64, 123003, apps)  # delete
    insert_role_right_for_system(64, 123004, apps)  # search
    insert_role_right_for_system(64, 123005, apps)  # create
    insert_role_right_for_system(64, 123006, apps)  # update
    insert_role_right_for_system(64, 123007, apps)  # delete


class Migration(migrations.Migration):

    dependencies = [
        ('grievance_social_protection', '0005_auto_20230703_1349'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='ticket_dueDate',
        ),
        migrations.AddField(
            model_name='ticket',
            name='ticket_due_date',
            field=models.DateField(blank=True, db_column='TicketDueDate', null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='date_of_incident',
            field=models.DateField(blank=True, db_column='IncidentDate', null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='date_submitted',
            field=core.fields.DateField(blank=True, db_column='SubmissionDate', default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='name_of_complainant',
            field=models.CharField(blank=True, db_column='ComplainantName', max_length=100, null=True),
        ),
        migrations.RunPython(add_rights),
    ]
