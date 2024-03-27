# Generated by Django 3.2.18 on 2023-04-25 16:38

import core.fields
import core.models
import datetime
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_add_last_login_on_interactive_user'),
        ('insuree', '0013_auto_20211103_1023'),
        ('location', '0008_add_enrollment_officer_gql_query_location_right'),
        ('grievance_social_protection', '0003_auto_20221130_1620'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachmentMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='attachment', to='core.mutationlog')),
            ],
            options={
                'db_table': 'ticket_AttachmentMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('validity_from', core.fields.DateTimeField(db_column='ValidityFrom', default=datetime.datetime.now)),
                ('validity_to', core.fields.DateTimeField(blank=True, db_column='ValidityTo', null=True)),
                ('legacy_id', models.IntegerField(blank=True, db_column='LegacyID', null=True)),
                ('json_ext', models.JSONField(blank=True, db_column='JsonExt', null=True)),
                ('id', models.AutoField(db_column='CategoryId', primary_key=True, serialize=False)),
                ('uuid', models.CharField(db_column='CategoryUUID', default=uuid.uuid4, max_length=36, unique=True)),
                ('category_title', models.CharField(blank=True, db_column='CategoryTitle', max_length=100, null=True)),
                ('slug', models.SlugField(blank=True, db_column='Slug', help_text='This is a label for each title which makes it easily identified', null=True, unique=True)),
            ],
            options={
                'db_table': 'tblCategory',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='CategoryMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='grievance_social_protection.category')),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='category', to='core.mutationlog')),
            ],
            options={
                'db_table': 'ticket_CategoryMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('validity_from', core.fields.DateTimeField(db_column='ValidityFrom', default=datetime.datetime.now)),
                ('validity_to', core.fields.DateTimeField(blank=True, db_column='ValidityTo', null=True)),
                ('legacy_id', models.IntegerField(blank=True, db_column='LegacyID', null=True)),
                ('id', models.AutoField(db_column='TicketId', primary_key=True, serialize=False)),
                ('uuid', models.CharField(db_column='TicketUUID', default=uuid.uuid4, max_length=36, unique=True)),
                ('ticket_title', models.CharField(blank=True, db_column='TicketTitle', max_length=255, null=True)),
                ('ticket_code', models.CharField(blank=True, db_column='TicketCode', max_length=8, null=True, unique=True)),
                ('ticket_description', models.TextField(blank=True, db_column='Description', max_length=255, null=True)),
                ('name', models.CharField(blank=True, db_column='Name', max_length=100, null=True)),
                ('phone', models.IntegerField(blank=True, db_column='PhoneNumber', null=True)),
                ('email', models.CharField(blank=True, db_column='Email', max_length=200, null=True)),
                ('date_of_incident', models.DateField(blank=True, db_column='Date_of_Incident', null=True)),
                ('name_of_complainant', models.CharField(blank=True, db_column='Name of Complainanat', max_length=100, null=True)),
                ('witness', models.CharField(blank=True, db_column='Witness', max_length=255, null=True)),
                ('insuree_location', models.CharField(blank=True, db_column='insureeLocation', max_length=50, null=True)),
                ('resolution', models.CharField(blank=True, db_column='Resolution', max_length=255, null=True)),
                ('ticket_status', models.TextField(choices=[('Waiting', 'Waiting'), ('Todo', 'Todo'), ('Inprogress', 'Inprogress'), ('Review', 'Review'), ('CLOSE', 'CLOSE')], db_column='TicketStatus', default='Waiting', max_length=15)),
                ('ticket_priority', models.CharField(choices=[('Critical', 'Critical'), ('High', 'high'), ('Normal', 'Normal'), ('Low', 'Low')], db_column='TicketPriority', default='Normal', help_text='how critical is the problem C = Critical and L = Low ', max_length=15)),
                ('ticket_dueDate', models.DateField(blank=True, db_column='Tciket_DueDate', null=True)),
                ('date_submitted', core.fields.DateField(blank=True, db_column='Date_Submission', default=datetime.datetime.now)),
                ('category', models.ForeignKey(blank=True, db_column='CategoryID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='tickets', to='grievance_social_protection.category')),
                ('event_location', models.ForeignKey(blank=True, db_column='EventLocationId', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='event_location', to='location.location')),
                ('insuree', models.ForeignKey(blank=True, db_column='InsureeID', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='tickets', to='insuree.insuree')),
            ],
            options={
                'db_table': 'tblTicket',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TicketAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('validity_from', core.fields.DateTimeField(db_column='ValidityFrom', default=datetime.datetime.now)),
                ('validity_to', core.fields.DateTimeField(blank=True, db_column='ValidityTo', null=True)),
                ('legacy_id', models.UUIDField(blank=True, db_column='LegacyID', null=True)),
                ('uuid', models.CharField(db_column='AttachmentUUID', default=uuid.uuid4, max_length=36, unique=True)),
                ('filename', models.TextField(blank=True, max_length=1000, null=True)),
                ('mime_type', models.TextField(blank=True, max_length=255, null=True)),
                ('url', models.TextField(blank=True, max_length=1000, null=True)),
                ('document', models.TextField(blank=True, null=True)),
                ('date', core.fields.DateField(blank=True, default=datetime.datetime.now)),
                ('ticket', models.ForeignKey(db_column='TicketId', on_delete=django.db.models.deletion.DO_NOTHING, related_name='attachment', to='grievance_social_protection.ticket')),
            ],
            options={
                'db_table': 'tblTicketAttachment',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TicketMutation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('mutation', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='tickets', to='core.mutationlog')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='grievance_social_protection.ticket')),
            ],
            options={
                'db_table': 'ticket_TicketMutation',
                'managed': True,
            },
            bases=(models.Model, core.models.ObjectMutation),
        ),
        migrations.RemoveField(
            model_name='grievancemutation',
            name='Grievance',
        ),
        migrations.RemoveField(
            model_name='grievancemutation',
            name='mutation',
        ),
        migrations.DeleteModel(
            name='Grievance',
        ),
        migrations.DeleteModel(
            name='GrievanceMutation',
        ),
        migrations.AddField(
            model_name='attachmentmutation',
            name='ticket',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='mutations', to='grievance_social_protection.ticketattachment'),
        ),
    ]
