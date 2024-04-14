from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from graphql import ResolveInfo

import core
from core import models as core_models
from core.models import HistoryBusinessModel, User, HistoryModel
from individual.models import Individual


def check_if_user_or_individual(generic_field):
    if not isinstance(generic_field, (User, Individual)):
        raise ValueError('Reporter must be either a User or an Individual.')


class Ticket(HistoryBusinessModel):
    class TicketStatus(models.TextChoices):
        # TMP FOR NOW
        RECEIVED = 'RECEIVED', 'Received'
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    key = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=16, unique=True, blank=True, null=True)

    reporter_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=False, blank=False)
    reporter_id = models.PositiveIntegerField(null=False, blank=False)
    reporter = GenericForeignKey('reporter_type', 'reporter_id')

    attending_staff = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    date_of_incident = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20, blank=False, null=False, choices=TicketStatus.choices, default=TicketStatus.RECEIVED
    )
    priority = models.CharField(max_length=20, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    def clean(self):
        super().clean()
        if self.reporter:
            check_if_user_or_individual(self.reporter)

    def __str__(self):
        return f"{self.title}"


    @classmethod
    def filter_queryset(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()
        queryset = queryset.filter(*core.filter_validity())
        return queryset

    @classmethod
    def get_queryset(cls, queryset, user):
        queryset = cls.filter_queryset(queryset)
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=None)
        if settings.ROW_SECURITY:
            pass
        return queryset


class TicketMutation(core_models.UUIDModel, core_models.ObjectMutation):
    ticket = models.ForeignKey(Ticket, models.DO_NOTHING,
                               related_name='mutations')
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name='tickets')

    class Meta:
        managed = True
        db_table = "ticket_TicketMutation"


class Comment(HistoryModel):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, null=False, blank=False)
    commenter_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=False, blank=False)
    commenter_id = models.PositiveIntegerField(null=False, blank=False)
    commenter = GenericForeignKey('commenter_type', 'commenter_id')
    comment = models.TextField(blank=False, null=False)

    def clean(self):
        super().clean()
        if self.commenter:
            check_if_user_or_individual(self.commenter)


# LEFT IF NEEDED IN THE FUTURE

# class TicketAttachment(core_models.UUIDModel, core_models.UUIDVersionedModel, ):
#     uuid = models.CharField(db_column='AttachmentUUID', max_length=36, default=uuid.uuid4, unique=True)
#     ticket = models.ForeignKey(
#         Ticket, models.DO_NOTHING, related_name='attachment', db_column='TicketId', blank=True, null=True)
#     filename = models.TextField(max_length=1000, blank=True, null=True)
#     mime_type = models.TextField(max_length=255, blank=True, null=True)
#     url = models.TextField(max_length=1000, blank=True, null=True)
#     document = models.TextField(blank=True, null=True)
#     date = fields.DateField(blank=True, default=py_datetime.now)
#
#     def __str__(self):
#         return f"{self.filename}"
#
#     def full_file_path(self):
#         if not TicketConfig.tickets_attachments_root_path or not self.filename:
#             return None
#         return os.path.join(TicketConfig.tickets_attachments_root_path, self.filename)
#
#     class Meta:
#         managed = True
#         db_table = 'tblTicketAttachment'
#
#     @classmethod
#     def filter_queryset(cls, queryset=None):
#         if queryset is None:
#             queryset = cls.objects.all()
#         queryset = queryset.filter(*core.filter_validity())
#         return queryset
#
#     @classmethod
#     def get_queryset(cls, queryset, user):
#         queryset = cls.filter_queryset(queryset)
#         if isinstance(user, ResolveInfo):
#             user = user.context.user
#         if settings.ROW_SECURITY and user.is_anonymous:
#             return queryset.filter(id=None)
#         if settings.ROW_SECURITY:
#             pass
#         return queryset


# LEFT IF NEEDED IN THE FUTURE

# class AttachmentMutation(core_models.UUIDModel, core_models.ObjectMutation):
#     ticket = models.ForeignKey(TicketAttachment, models.DO_NOTHING,
#                                related_name='mutations')
#     mutation = models.ForeignKey(
#         core_models.MutationLog, models.DO_NOTHING, related_name='attachment')
#
#     class Meta:
#         managed = True
#         db_table = "ticket_AttachmentMutation"
