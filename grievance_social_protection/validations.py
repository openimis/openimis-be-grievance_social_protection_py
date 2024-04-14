from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType

from core.validation import BaseModelValidation
from grievance_social_protection.models import Ticket


class TicketValidation(BaseModelValidation):
    OBJECT_TYPE = Ticket

    @classmethod
    def validate_create(cls, user, **data):
        errors = [
            *validate_ticket_unique_code(data),
            *validate_reporter(data)
        ]
        if errors:
            raise ValidationError(errors)

    @classmethod
    def validate_update(cls, user, **data):
        errors = [
            *validate_ticket_unique_code(data),
            *validate_reporter(data)
        ]
        if errors:
            raise ValidationError(errors)


def validate_ticket_unique_code(data):
    code = data.get('code')
    ticket_id = data.get('id')

    if not code:
        return []

    ticket_queryset = Ticket.objects.filter(code=code)
    if ticket_id:
        ticket_queryset.exclude(id=ticket_id)
    if ticket_queryset.exists():
        return [{"message": _("validations.TicketValidation.validate_ticket_unique_code") % {"code": code}}]
    return []


def validate_reporter(data):
    reporter_type = data.get("reporter_type")
    reporter_id = data.get("reporter_id")

    if reporter_type and reporter_id:
        if reporter_type not in ["User", "Individual"]:
            return [{"message": _("validations.TicketValidation.invalid_reporter_type")}]

        try:
            content_type = ContentType.objects.get(model=reporter_type.lower())
        except Exception:
            return [{"message": _("validations.TicketValidation.reporter_type_invalid")}]

        try:
            content_type.get_object_for_this_type(id=reporter_id)
        except Exception:
            return [{"message": _("validations.TicketValidation.reporter_not_found")}]

        return []

    error_messages = []
    if not reporter_type:
        error_messages.append({"message": _("validations.TicketValidation.reporter_type_required")})
    if not reporter_id:
        error_messages.append({"message": _("validations.TicketValidation.reporter_id_required")})

    return error_messages
