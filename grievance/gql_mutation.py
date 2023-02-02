from typing_extensions import Required
import graphene
from core import prefix_filterset, ExtendedConnection, filter_validity, Q, assert_string_length
from core.schema import TinyInt, SmallInt, OpenIMISMutation, OrderedDjangoFilterConnectionField
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext as _
from graphene.relay import mutation
from .apps import GrievanceConfig
from graphene import InputObjectType
from .models import *

class GrievanceInputType(OpenIMISMutation.Input):
    
    id = graphene.Int(required=False, read_only=True)
    uuid = graphene.String(required=False)
    insuree_uuid = graphene.String(required=True)
    creation_date = graphene.String(required=False)
    status = graphene.String(required=False)
    description = graphene.String(required=False)
    type_of_grievance = graphene.String(required=False)
    comments = graphene.String(required=False)
    created_by = graphene.String(required=False)
    close_date = graphene.String(required=False)
    grievance_code = graphene.String(required=False)


   #This section create or update grievance mutation....
def update_or_create_grievance(data, user):

    # Check if client_mutation_id is passed in data
    if "client_mutation_id" in data:
        data.pop('client_mutation_id')
    # Check if client_mutation_label is passed in data
    if "client_mutation_label" in data:
        data.pop('client_mutation_label')
    
    grievanceID = data.pop('uuid') if 'uuid' in data else None

    if grievanceID:
        # fetch grievance by uuid
        grievance = Grievance.objects.get(uuid=grievanceID)
        [setattr(grievance, key, data[key]) for key in data]
    else:
        # create new grievance object
        grievance = Grievance.objects.create(**data)
        
    # save record to database
    grievance.save()
    return grievance

class CreateOrUpdateGrievanceMutation(OpenIMISMutation):
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
        
        #This create instance of insuree and sschem
        insuree = data.pop('insuree_uuid')

        prinsuree =Insuree.objects.get(uuid=insuree)

        data['insuree'] = prinsuree
        
        # calles the create and update method and returns the created record from the Grievances object
        grievance = update_or_create_grievance(data, user)

        # log mutation through signal binding everytime a mutation occur
        GrievanceMutation.object_mutated(user, Grievance=grievance)
        
        return None
    #End of create or update grievance


# This class create mtation for service provider.....
class CreateGrievanceMutation(CreateOrUpdateGrievanceMutation):
    _mutation_module = "grievance"
    _mutation_class = "CreateGrievanceMutation"

    class Input(GrievanceInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            """
            Calls the do_mutate defiend in CreateGrievanceMutation that checks permission
            and call update_or_create_grievance to perform the update on the grievance record.
            """
            return cls.do_mutate(GrievanceConfig.gql_mutation_create_grievance_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Grievance mutation failed",
                'detail': str(exc)}]
    #End of Grievance Mutation section...................
    
  
class UpdateGrievanceMutation(CreateOrUpdateGrievanceMutation):
    """
    Update an existing Grievance
    """
    _mutation_module = "grievance"
    _mutation_class = "UpdateGrievanceMutation"

    # Sets the input type of this mutation
    class Input(GrievanceInputType):
        pass

    @classmethod
    def async_mutate(cls, user, **data):
        try:
            """
            Calls the do_mutate defiend in CreateGrievanceMutation that checks permission
            and call update_or_create_grievance to perform the update on the Grievance record.
            """
            return cls.do_mutate(GrievanceConfig.gql_mutation_update_grievance_perms, user, **data)
        except Exception as exc:
            return [{
                'message': "Grievance mutation update failed with exceptions",
                'detail': str(exc)}
            ]
#End of update prorams

    
    #This class delete Grievance mutation....
class DeleteGrievanceMutation(OpenIMISMutation):
    _mutation_module = "grievance"
    _mutation_class = "DeleteGrievanceMutation"

    class Input(OpenIMISMutation.Input):
        
        uuid = graphene.String()
        
        
                        
    @classmethod
    def async_mutate(cls, user, **data):
        try:
            # Check if user has permission
            if not user.has_perms(GrievanceConfig.gql_mutation_delete_grievance_perms):
                raise PermissionDenied(_("unauthorized"))

            # get Grievance object by uuid
            grievance = Grievance.objects.get(uuid=data['uuid'])

            # get current date time
            from core import datetime
            now = datetime.datetime.now()

            # Set validity_to to now to make the record invalid
            grievance.validity_to = now
            grievance.save()
            return None
        except Exception as exc:
            return [{
                'message': "Faild to delete Grievance provider. An exception had occured",
                'detail': str(exc)}]
    #End of delete service provider subLevel mutation....