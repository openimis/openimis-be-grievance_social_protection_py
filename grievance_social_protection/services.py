from django.contrib.contenttypes.models import ContentType
from django.db.models import Max

from core.services import BaseService
from core.signals import register_service_signal
from grievance_social_protection.models import Ticket
from grievance_social_protection.validations import TicketValidation


class TicketService(BaseService):
    OBJECT_TYPE = Ticket

    def __init__(self, user, validation_class=TicketValidation):
        super().__init__(user, validation_class)

    @register_service_signal('ticket_service.create')
    def create(self, obj_data):
        self.validation_class.validate_create(self.user, **obj_data)
        self._get_content_type(obj_data)
        self._generate_code(obj_data)
        return super().create(obj_data)

    @register_service_signal('ticket_service.update')
    def update(self, obj_data):
        self.validation_class.validate_update(self.user, **obj_data)
        self._get_content_type(obj_data)
        return super().update(obj_data)


    @register_service_signal('ticket_service.delete')
    def delete(self, obj_data):
        return super().delete(obj_data)

    def _get_content_type(self, obj_data):
        content_type = ContentType.objects.get(model=obj_data['reporter_type'].lower())
        obj_data['reporter_type'] = content_type


    def _generate_code(self, obj_data):
        if not obj_data.get('code'):
            last_ticket_code = Ticket.objects.filter(code__startswith='GRS').aggregate(Max('code')).get('code__max')
            if last_ticket_code is None:
                last_ticket_code_numeric = 0
            else:
                last_ticket_code_numeric = int(last_ticket_code[3:])

            new_ticket_code = f'GRS{last_ticket_code_numeric + 1:08}'
            obj_data['code'] = new_ticket_code
