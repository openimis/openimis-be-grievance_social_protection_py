import graphene
from graphene_django import DjangoObjectType
from .models import Ticket, Category, TicketAttachment
from insuree.schema import InsureeGQLType
from core import prefix_filterset, ExtendedConnection, filter_validity, ExtendedRelayConnection


class CategoryTicketGQLType(DjangoObjectType):
    """
    create a category with a label in the slug field
    """

    class Meta:
        model = Category
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "uuid": ['exact'],
            "uuid": ["exact"],
            "category_title": ["exact", "istartswith", "icontains", "iexact"],
            "slug": ["exact", "istartswith", "icontains", "iexact"]
        }
        connection_class = ExtendedConnection


class TicketGQLType(DjangoObjectType):
    client_mutation_id = graphene.String()

    def resolve_insuree(self, info):
        if "insuree_loader" in info.context.dataloaders and self.insuree_id:
            return info.context.dataloaders["insuree_loader"].load(self.insuree_id)
        return self.insuree

    class Meta:
        model = Ticket
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "uuid": ["exact"],
            "ticket_title": ["exact", "istartswith", "icontains", "iexact"],
            "ticket_code": ["exact", "istartswith", "icontains", "iexact"],
            "ticket_description": ["exact", "istartswith", "icontains", "iexact"],
            "name": ["exact", "istartswith", "icontains", "iexact"],
            "phone": ["exact", "istartswith", "icontains", "iexact"],
            "email": ["exact", "istartswith", "icontains", "iexact"],
            "date_of_incident": ["exact", "istartswith", "icontains", "iexact"],
            "name_of_complainant": ["exact", "istartswith", "icontains", "iexact"],
            "witness": ["exact", "istartswith", "icontains", "iexact"],
            "resolution": ["exact", "istartswith", "icontains", "iexact"],
            "ticket_status": ["exact", "istartswith", "icontains", "iexact"],
            "ticket_priority": ["exact", "istartswith", "icontains", "iexact"],
            "ticket_due_date": ["exact", "istartswith", "icontains", "iexact"],
            "date_submitted": ["exact", "istartswith", "icontains", "iexact"],
            **prefix_filterset("category__", CategoryTicketGQLType._meta.filter_fields),
            **prefix_filterset("insuree__", InsureeGQLType._meta.filter_fields),
            # **prefix_filterset("location__", LocationGQLType._meta.filter_fields)
        }

        connection_class = ExtendedConnection

    def resolve_client_mutation_id(self, info):
        ticket_mutation = self.mutations.select_related(
            'mutation').filter(mutation__status=0).first()
        return ticket_mutation.mutation.client_mutation_id if ticket_mutation else None


class TicketAttachmentGQLType(DjangoObjectType):
    class Meta:
        model = TicketAttachment
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "filename": ["exact", "icontains"],
            "mime_type": ["exact", "icontains"],
            "url": ["exact", "icontains"],
            **prefix_filterset("ticket__", TicketGQLType._meta.filter_fields),
        }
        connection_class = ExtendedConnection

    @classmethod
    def get_queryset(cls, queryset, info):
        queryset = queryset.filter(*filter_validity())
        return queryset
