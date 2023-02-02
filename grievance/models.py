from django.db import models
import uuid
from core import models as core_models
from insuree.models import *

grievance_type = (
    ('Inquiry','Inquiry'),
    ('Problem', 'Problem'),
    ('General', 'General'),
)

status = (
    ('Open','Open'),
    ('Close', 'Close'),
    ('In Progress', 'In Progress'),
)

# Create your models here.
class Grievance(core_models.VersionedModel):
    id = models.AutoField(
        db_column='grievanceID', primary_key=True)
        
    uuid = models.CharField(db_column='grievanceUUID', max_length=36, default=uuid.uuid4, unique=True)

    grievance_code = models.CharField(max_length=15, db_column='grievanceCode', unique=True, null=True)
    insuree = models.ForeignKey(Insuree, on_delete=models.DO_NOTHING, null=True)
    creation_date = models.DateField(db_column='creationDate', blank=True, null=True)
    status = models.CharField(db_column='Status', max_length=36, choices=status, default='Open')
    description = models.CharField(db_column='description', max_length=255, blank=True, null=True)
    type_of_grievance = models.CharField(db_column='typeOfGrievance', max_length=36, choices=grievance_type, default='General')
    comments = models.CharField(db_column='comments', max_length=255, blank=True, null=True)
    created_by = models.CharField(db_column='createdBy', max_length=255, blank=True, null=True)
    close_date = models.DateField(db_column='closeDate', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tblGrievance'



class GrievanceMutation(core_models.UUIDModel, core_models.ObjectMutation):
    Grievance = models.ForeignKey(Grievance, models.DO_NOTHING, related_name='mutations')
    mutation = models.ForeignKey(core_models.MutationLog, models.DO_NOTHING, related_name='Grievance')

    class Meta:
        managed = True
        db_table = "GrievanceMutation"

