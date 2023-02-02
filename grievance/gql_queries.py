import graphene
from graphene_django import DjangoObjectType
from core import prefix_filterset, filter_validity, ExtendedConnection
from .models import *


class GrievanceGQLType(DjangoObjectType):

    class Meta:
        model = Grievance
        filter_fields = {
            "insuree": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "creation_date": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "status": ["exact", "lt", "lte", "gt", "gte"],
            "description": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "type_of_grievance": ["exact", "lt", "lte", "gt", "gte"],
            "comments": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "created_by": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "close_date": ["exact", "lt", "lte", "gt", "gte", "isnull"],
            "grievance_code": ["exact", "lt", "lte", "gt", "gte", "isnull"],
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExtendedConnection
