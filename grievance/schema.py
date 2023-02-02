from configparser import DuplicateOptionError
from multiprocessing.reduction import duplicate
from core.schema import signal_mutation_module_validate
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from graphene_django.filter import DjangoFilterConnectionField
import graphene_django_optimizer as gql_optimizer
from django.utils.translation import gettext as _
from location.apps import LocationConfig
from core.schema import OrderedDjangoFilterConnectionField, OfficerGQLType
from policy.models import Policy

# We do need all queries and mutations in the namespace here.
from .gql_queries import *  # lgtm [py/polluting-import]
from .gql_mutation import *  # lgtm [py/polluting-import]

class Query(graphene.ObjectType):
    grievance = OrderedDjangoFilterConnectionField(
        GrievanceGQLType,
        show_history=graphene.Boolean(),
        client_mutation_id=graphene.String(),
        orderBy=graphene.List(of_type=graphene.String),
    )
    grievancesStr = OrderedDjangoFilterConnectionField(
        GrievanceGQLType,
        str=graphene.String(),
    )

def resolve_grievances(self, info, **kwargs):
        """
        Extra steps to perform when Scheme is queried
        """
        # Check if user has permission
        if not info.context.user.has_perms(GrievanceConfig.gql_query_grievance_perms):
            raise PermissionDenied(_("unauthorized"))
        filters = []
        
        # Used to specify if user want to see all records including invalid records as history
        show_history = kwargs.get('show_history', False)
        if not show_history:
            filters += filter_validity(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        return gql_optimizer.query(Grievance.objects.filter(*filters).all(), info)

def resolve_grievancesStr(self, info, **kwargs):
        """
        Extra steps to perform when Scheme is queried
        """
        # Check if user has permission
        if not info.context.user.has_perms(GrievanceConfig.gql_query_grievance_perms):
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

        return gql_optimizer.query(Grievance.objects.filter(*filters).all(), info)


class Mutation(graphene.ObjectType):
    """
    QraphQL Mutation for schemes
    """
    create_grievance = CreateGrievanceMutation.Field()
    update_grievance = UpdateGrievanceMutation.Field()
    delete_grievancek = DeleteGrievanceMutation.Field()


def on_grievance_mutation(kwargs, k='uuid'):
    """
    This method is called on signal binding for scheme mutation
    """

    # get uuid from data
    grievance_uuid = kwargs['data'].get('uuid', None)
    if not grievance_uuid:
        return []
    # fetch the scheme object by uuid
    impacted_grievance = Grievance.objects.get(Q(uuid=grievance_uuid))
    # Create a mutation object
    GrievanceMutation.objects.create(grievance=impacted_grievance, mutation_id=kwargs['mutation_log_id'])
    return []

def on_grievance_mutation(kwargs):
    """
    This method is called on signal binding for scheme mutation 
    of multiple records
    """
    uuids = kwargs['data'].get('uuids', [])
    if not uuids:
        uuid = kwargs['data'].get('uuid', None)
        uuids = [uuid] if uuid else []
    if not uuids:
        return []
    impacted_grievances = Grievance.objects.filter(uuid_in=uuids).all()
    for grievance in impacted_grievances:
        Grievance.objects.create(
            Grievance=grievance, mutation_id=kwargs['mutation_log_id'])
    return []
    