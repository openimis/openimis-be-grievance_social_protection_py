import graphene
from graphene_django import DjangoObjectType
from ticket.models import Ticket, Category, TicketAttachment
from insuree.schema import InsureeGQLType
from location.schema import LocationGQLType
from core import prefix_filterset, ExtendedConnection, filter_validity




class CategoryTicketGQLType(DjangoObjectType):

    """
    create a category with a label in the slug field
    """

    class Meta:
        model = Category
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id":["exact"],
            "uuid": ['exact'], 
            "uuid":["exact"],
            "category_title":["exact", "istartswith", "icontains", "iexact"],
            "slug":["exact", "istartswith", "icontains", "iexact"]
        }
        connection_class = ExtendedConnection




class TicketGQLType (DjangoObjectType):

    client_mutation_id = graphene.String()

    def resolve_insuree(self, info):
        if "insuree_loader" in info.context.dataloaders and self.insuree_id:
            return info.context.dataloaders["insuree_loader"].load(self.insuree_id)
        return self.insuree



    class Meta:

        model = Ticket
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id":["exact"],
            "uuid":["exact"],
            "ticket_title": ["exact"],
            "ticket_code":["exact"],
            "ticket_description" : ["exact" ],
            "name":["exact"],
            "phone":["exact"],
            "email":["exact"],
            "date_of_incident":["exact"],
            "name_of_complainant":["exact"],
            "witness":["exact"],
            "resolution":["exact"],
            "ticket_status": ["exact"],
            "ticket_priority": ["exact"],
            "ticket_dueDate":["exact"],
            "date_submitted":["exact"],
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


    