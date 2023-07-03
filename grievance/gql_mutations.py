import pathlib
import graphene
import uuid
import base64
from graphene import InputObjectType
from core import filter_validity, assert_string_length
from core.schema import OpenIMISMutation
from .models import Ticket, TicketMutation, Category, CategoryMutation, TicketAttachment, AttachmentMutation
from insuree.models import Insuree
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from .apps import TicketConfig
from django.utils.translation import gettext_lazy as _
from django.db.models import Max
from django.utils import timezone


class CategoryInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    category_title = graphene.String(required=False)
    slug = graphene.String(required=False)


class TicketCodeInputType(graphene.String):

    @staticmethod
    def coerce_string(value):
        assert_string_length(value, 8)
        return value

    serialize = coerce_string
    parse_value = coerce_string

    @staticmethod
    def parse_literal(ast):
        result = graphene.String.parse_literal(ast)
        assert_string_length(result, 8)
        return result


class TicketInputType(OpenIMISMutation.Input):
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    ticket_code = graphene.String(required=False)
    ticket_title = graphene.String(required=False)
    ticket_description = graphene.String(required=False)
    category_uuid = graphene.String(required=False)
    insuree_uuid = graphene.String(required=False)
    name = graphene.String(required=False)
    phone = graphene.String(required=False)
    email = graphene.String(required=False)
    # location_uuid = graphene.String(required = False)
    date_of_incident = graphene.Date(required=False)
    witness = graphene.String(required=False)
    name_of_complainant = graphene.String(required=False)
    resolution = graphene.String(required=False)
    ticket_status = graphene.String(required=False)
    ticket_priority = graphene.String(required=False)
    ticket_dueDate = graphene.Date(required=False)
    date_submitted = graphene.Date(required=False)


class BaseAttachment:
    id = graphene.String(required=False, read_only=True)
    uuid = graphene.String(required=False)
    filename = graphene.String(required=False)
    mime_type = graphene.String(required=False)
    url = graphene.String(required=False)
    date = graphene.Date(required=False)


class BaseAttachmentInputType(BaseAttachment, OpenIMISMutation.Input):
    """
    Ticket attachment (without the document), used on its own
    """
    ticket_uuid = graphene.String(required=False)


class Attachment(BaseAttachment):
    document = graphene.String(required=False)


class TicketAttachmentInputType(Attachment, InputObjectType):
    """
    Ticket attachment, used nested in claim object
    """
    pass


class AttachmentInputType(Attachment, OpenIMISMutation.Input):
    """
    Ticket attachment, used on its own
    """
    ticket_uuid = graphene.String(required=False)


def create_file(date, ticket_id, document):
    date_iso = date.isoformat()
    root = TicketConfig.tickets_attachments_root_path
    file_dir = '%s/%s/%s/%s' % (
        date_iso[0:4],
        date_iso[5:7],
        date_iso[8:10],
        ticket_id
    )

    file_path = '%s/%s' % (file_dir, uuid.uuid4())
    pathlib.Path('%s/%s' % (root, file_dir)).mkdir(parents=True, exist_ok=True)
    f = open('%s/%s' % (root, file_path), "xb")
    f.write(base64.b64decode(document))
    f.close()
    return file_path


def create_attachment(ticket_id, data):
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    # Check if client_mutation_label is passed in data
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    data['ticket_id'] = ticket_id
    now = timezone.now()
    if TicketConfig.tickets_attachments_root_path:
        data['url'] = create_file(now, ticket_id, data.pop('document'))
    data['validity_from'] = now
    attachment = TicketAttachment.objects.create(**data)
    attachment.save()
    return attachment


def create_attachments(ticket_id, attachments):
    for attachment in attachments:
        create_attachment(ticket_id, attachment)


def update_or_create_category(data, user):
    # Check if client_mutation_id is passed in data
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    # Check if client_mutation_label is passed in data
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    # get ticket_uuid from data
    category_uuid = data.pop('uuid') if 'uuid' in data else None
    if category_uuid:
        # fetch ticket by uuid
        category = Category.objects.get(uuid=category_uuid)
        [setattr(category, key, data[key]) for key in data]
    else:
        # create new Ticket object
        category = Category.objects.create(**data)
    # save record to database
    category.save()
    return category


def update_or_create_ticket(data, user):
    # Check if client_mutation_id is passed in data
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    # Check if client_mutation_label is passed in data
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')

    ticket_uuid = data.pop('uuid') if 'uuid' in data else None
    if ticket_uuid:
        # fetch ticket by uuid
        ticket = Ticket.objects.get(uuid=ticket_uuid)
        [setattr(ticket, key, data[key]) for key in data]
    else:
        # create new Ticket object
        ticket = Ticket.objects.create(**data)
    # save record to database
    ticket.save()
    return ticket


class CreateOrUpdateCategoryMutation(OpenIMISMutation):
    @classmethod
    def do_mutate(cls, perms, user, **data):
        # Check if user is authenticated
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError(
                _("mutation.authentication_required"))

        # Check if user has permission
        if not user.has_perms(perms):
            raise PermissionDenied(_("unauthorized"))

        # data['audit_user_id'] = user.id_for_audit
        from core.utils import TimeUtils
        data['validity_from'] = TimeUtils.now()

        # get client_mutation_id from data
        client_mutation_id = data.get("client_mutation_id")

        # calles the create and update method and returns the created record from the Bank object
        category = update_or_create_category(data, user)

        # log mutation through signal binding everytime a mutation occur
        CategoryMutation.object_mutated(user, client_mutation_id=client_mutation_id, Category=category)
        return None


class CreateOrUpdateTicketMutation(OpenIMISMutation):

    @classmethod
    def do_mutate(cls, perms, user, **data):
        # Check if user is authenticated
        if type(user) is AnonymousUser or not user.id:
            raise ValidationError(
                _("mutation.authentication_required"))

        # Check if user has permission
        if not user.has_perms(perms):
            raise PermissionDenied(_("unauthorized"))

        last_ticket_code = Ticket.objects.aggregate(Max('ticket_code')).get('ticket_code__max')
        if last_ticket_code is None:
            last_ticket_code_numeric = 0
        else:
            last_ticket_code_numeric = int(last_ticket_code[3:])

        new_ticket_code = f'GRS{last_ticket_code_numeric + 1:08}'

        # Generate ticket code if not present in data
        if data.get('ticket_code', None) is None:
            data['ticket_code'] = new_ticket_code

        # Get the maximum ticket code from the database

        # if Ticket.objects.filter(ticket_code = data['ticket_code']).exists():
        #     return [{
        #             'message': _("tciket.mutation.duplicated_ticket_code") % {'ticket_code': data['ticket_code']},
        #         }]

        # data['audit_user_id'] = user.id_for_audit
        from core.utils import TimeUtils
        data['validity_from'] = TimeUtils.now()

        # get client_mutation_id from data
        client_mutation_id = data.get("client_mutation_id")

        # This create instance of insuree and category and location
        category = data.pop('category_uuid')
        insuree = data.pop('insuree_uuid')

        ticketcategory = Category.objects.get(uuid=category)
        ticketinsuree = Insuree.objects.get(uuid=insuree)

        data['category'] = ticketcategory
        data['insuree'] = ticketinsuree

        # calles the create and update method and returns the created record from the Ticket object
        ticket = update_or_create_ticket(data, user)
        # log mutation through signal binding everytime a mutation occur
        TicketMutation.object_mutated(user, client_mutation_id=client_mutation_id, Ticket=ticket)

        return None


class CreateTicketMutation(CreateOrUpdateTicketMutation):
    """
    Create a new ticket. 
    """
    _mutation_module = "grievance"
    _mutation_class = "CreateTicketMutation"

    class Input(TicketInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            """
            Calls the do_mutate defiend in CreateOrUpdateTicketMutation that checks permission
            and call update_or_create_Ticket to perform the creation on Ticket record.
            """

            return cls.do_mutate(TicketConfig.gql_mutation_create_tickets_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Ticket mutation failed with exceptions" % {'ticket_code': data['ticket_code']},
                'detail': str(exc)}]


class UpdateTicketMutation(CreateOrUpdateTicketMutation):
    """
   Update ticket.
   """
    _mutation_module = "grievance"
    _mutation_class = "UpdateTicketMutation"

    class Input(TicketInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):

        try:
            """
            Calls the do_mutate defiend in CreateOrUpdateTicketMutation that checks permission
            and call update_or_create_Ticket to perform the creation on Ticket record.
            """
            return cls.do_mutate(TicketConfig.gql_mutation_update_tickets_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Ticket mutation failed with exceptions" % {'ticket_code': data['ticket_code']},
                'detail': str(exc)}]


class DeleteTicketMutation(OpenIMISMutation):
    _mutation_module = 'ticket'
    _mutation_class = 'DeleteTicketMutation'

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):

        try:
            # Check if user has permission
            if not user.has_perms(TicketConfig.gql_mutation_delete_tickets_perms):
                raise PermissionDenied(_("unauthorized"))

            # get programs object by uuid
            ticket = Ticket.objects.get(uuid=data['uuid'])

            # get current date time
            from core import datetime
            now = datetime.datetime.now()

            # Set validity_to to now to make the record invalid
            ticket.validity_to = now
            ticket.save()
            return None
        except Exception as exc:
            return [{
                'message': "Faild to delete Ticket. An exception had occured",
                'detail': str(exc)}]


class CreateCategoryMutation(CreateOrUpdateCategoryMutation):
    """
    Create a new ticket. 
    """
    _mutation_module = "grievance"
    _mutation_class = "CreateCategoryMutation"

    class Input(CategoryInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            """
            Calls the do_mutate defiend in CreateOrUpdateTicketMutation that checks permission
            and call update_or_create_Ticket to perform the creation on Ticket record.
            """
            return cls.do_mutate(TicketConfig.gql_mutation_create_categorys_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Ticket mutation failed with exceptions",
                'detail': str(exc)}]


class UpdateCategoryMutation(CreateOrUpdateCategoryMutation):
    """
    Create a new ticket. 
    """
    _mutation_module = "grievance"
    _mutation_class = "UpdateCategoryMutation"

    class Input(CategoryInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            """
            Calls the do_mutate defiend in CreateOrUpdateTicketMutation that checks permission
            and call update_or_create_Ticket to perform the creation on Ticket record.
            """
            return cls.do_mutate(TicketConfig.gql_mutation_update_categorys_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Ticket mutation failed with exceptions",
                'detail': str(exc)}]


class DeleteCategoryMutation(OpenIMISMutation):
    _mutation_module = 'ticket'
    _mutation_class = 'DeleteCategoryMutation'

    class Input(OpenIMISMutation.Input):
        uuid = graphene.String()

    @classmethod
    def async_mutate(cls, user, **data):

        try:
            # Check if user has permission
            if not user.has_perms(TicketConfig.gql_mutation_delete_categorys_perms):
                raise PermissionDenied(_("unauthorized"))

            # get programs object by uuid
            ticket = Category.objects.get(uuid=data['uuid'])

            # get current date time
            from core import datetime
            now = datetime.datetime.now()

            # Set validity_to to now to make the record invalid
            ticket.validity_to = now
            ticket.save()
            return None
        except Exception as exc:
            return [{
                'message': "Faild to delete Category. An exception had occured",
                'detail': str(exc)}]


class CreateTicketAttachmentMutation(OpenIMISMutation):
    _mutation_module = "grievance"
    _mutation_class = "CreateTicketAttachmentMutation"

    class Input(AttachmentInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        ticket = None
        try:
            if user.is_anonymous or not user.has_perms(TicketConfig.gql_mutation_update_tickets_perms):
                raise PermissionDenied(_("unauthorized"))
            if "client_mutation_id" in data:
                data.pop('client_mutation_id')
            if "client_mutation_label" in data:
                data.pop('client_mutation_label')
            ticket_uuid = data.pop('ticket_uuid')
            queryset = Ticket.objects.filter(*filter_validity())
            ticket = queryset.filter(uuid=ticket_uuid).first()
            if not ticket:
                raise PermissionDenied(_("unathorized"))
            create_attachment(ticket.id, data)
            return None
        except Exception as exc:
            return [{
                'message': _("ticket.mutation.failed_to_attach_document"),
                'detail': str(exc)}]


class UpdateTicketAttachmentMutation(OpenIMISMutation):
    _mutation_module = "grievance"
    _mutation_class = "UpdateTicketAttachmentMutation"

    class Input(BaseAttachmentInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):

        try:
            if not user.has_perms(TicketConfig.gql_mutation_update_tickets_perms):
                raise PermissionDenied(_("unauthorized"))
            # get ticketattachment uuid
            ticketattachment_uuid = data.pop('uuid')
            queryset = TicketAttachment.objects.filter(*filter_validity())
            if ticketattachment_uuid:
                # fetch ticketattachment uuid
                ticketattachment = queryset.filter(uuid=ticketattachment_uuid).first()
                [setattr(ticketattachment, key, data[key]) for key in data]
            else:
                # raise an error if uuid is not valid or does not exist
                raise PermissionDenied(_("unauthorized"))
            # saves update dta
            ticketattachment.save()
            return None
        except Exception as exc:
            return [{

                'message': _("ticket.mutation.failed_to_attach_document"),
                'detail': str(exc)}]
