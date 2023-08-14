from core.schema import OrderedDjangoFilterConnectionField, OpenIMISMutation
from core.schema import signal_mutation_module_validate
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q
import graphene_django_optimizer as gql_optimizer
from .gql_queries import *
from .gql_mutations import *
from django.utils.translation import gettext_lazy as _



class Query(graphene.ObjectType):
    tickets = OrderedDjangoFilterConnectionField(
        TicketGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        show_history=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    category = OrderedDjangoFilterConnectionField(
        CategoryTicketGQLType,
        client_mutation_id=graphene.String(),
        orderBy=graphene.List(of_type=graphene.String),
        show_history=graphene.Boolean(),
    )

    ticketsStr = OrderedDjangoFilterConnectionField(
        TicketGQLType,
        str=graphene.String(),
    )
    ticket_attachments = DjangoFilterConnectionField(TicketAttachmentGQLType)

    ticket_details = OrderedDjangoFilterConnectionField(
        TicketGQLType,
        ticket_uuid=graphene.String(required=True),
        # showHistory=graphene.Boolean(),
        orderBy=graphene.List(of_type=graphene.String),
    )

    def resolve_ticket_details(self, info, **kwargs):
        # if not info.context.user.has_perms(ServiceProviderConfig.gql_query_service_provider_perms):
        #     raise PermissionDenied(_("unauthorized"))
        ticket = Ticket.objects.get(
            Q(uuid=kwargs.get('ticket_uuid')))

        return Ticket.objects.filter(
            Q(uuid=ticket.uuid),
            *filter_validity(**kwargs)
        ).order_by('ticket_title', 'ticket_code', )

    def resolve_ticket(self, info, **kwargs):
        """
        Extra steps to perform when Scheme is queried
        """
        # Check if user has permission
        if not info.context.user.has_perms(TicketConfig.gql_query_tickets_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []

        # Used to specify if user want to see all records including invalid records as history
        show_history = kwargs.get('show_history', False)
        if not show_history:
            filters += filter_validity(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        return gql_optimizer.query(Ticket.objects.filter(*filters).all(), info)

    def resolve_ticketsStr(self, info, **kwargs):
        """
        Extra steps to perform when Scheme is queried
        """
        # Check if user has permission
        if not info.context.user.has_perms(TicketConfig.gql_query_tickets_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []

        # Used to specify if user want to see all records including invalid records as history
        show_history = kwargs.get('show_history', False)
        if not show_history:
            filters += filter_validity(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        # str = kwargs.get('str')
        # if str is not None:
        #     filters += [Q(code__icontains=str) | Q(name__icontains=str)]

        return gql_optimizer.query(Ticket.objects.filter(*filters).all(), info)

    def resolve_claim_attachments(self, info, **kwargs):
        if not info.context.user.has_perms(TicketConfig.gql_query_tickets_perms):
            raise PermissionDenied(_("unauthorized"))


class Mutation(graphene.ObjectType):
    create_Ticket = CreateTicketMutation.Field()
    update_Ticket = UpdateTicketMutation.Field()
    delete_Ticket = DeleteTicketMutation.Field()
    create_category = CreateCategoryMutation.Field()
    update_category = UpdateCategoryMutation.Field()
    delete_ticket = DeleteCategoryMutation.Field()
    create_ticket_attachment = CreateTicketAttachmentMutation.Field()
    update_ticket_attachment = UpdateTicketAttachmentMutation.Field()


def on_bank_mutation(kwargs, k='uuid'):
    """
    This method is called on signal binding for scheme mutation
    """

    # get uuid from data
    ticket_uuid = kwargs['data'].get('uuid', None)
    if not ticket_uuid:
        return []
    # fetch the scheme object by uuid
    impacted_ticket = Ticket.objects.get(Q(uuid=ticket_uuid))
    # Create a mutation object
    TicketMutation.objects.create(Bank=impacted_ticket, mutation_id=kwargs['mutation_log_id'])
    return []


def on_ticket_mutation(**kwargs):
    uuids = kwargs["data"].get("uuids", [])
    if not uuids:
        uuid = kwargs["data"].get("claim_uuid", None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_tickets = Ticket.objects.filter(uuid__in=uuids).all()
    for ticket in impacted_tickets:
        TicketMutation.objects.create(Ticket=ticket, mutation_id=kwargs["mutation_log_id"])
    return []


def bind_signals():
    signal_mutation_module_validate["grievance"].connect(on_ticket_mutation)
