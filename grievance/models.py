from django.conf import settings
from graphql import ResolveInfo
from django.db import models
from core import models as core_models
from core import fields, TimeUtils
from insuree import models as insuree_models
from location import models as location_models
from datetime import datetime as py_datetime
from .apps import TicketConfig
import core
import os.path
import random 

# Create your models here.
from django.utils.translation import gettext_lazy as _
import uuid
from core import models as core_models



# Create your models here.

#Categort Model
class Category(core_models.VersionedModel, core_models.ExtendableModel):

   id = models.AutoField(db_column='CategoryId', primary_key=True)
   uuid = models.CharField(db_column='CategoryUUID', max_length=36, default=uuid.uuid4, unique=True)
   category_title = models.CharField(db_column='CategoryTitle', max_length= 100, blank = True, null = True)
   slug = models.SlugField(db_column= "Slug", 
                           max_length= 50, 
                           unique= True,
                           help_text= "This is a label for each title which makes it easily identified",
                           blank = True,
                           null = True)
   

   def __str__(self):
        return str(self.category_title)

   
   class Meta:
        managed = True
        db_table = 'tblCategory'

    
   @classmethod
   def filter_queryset(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all() 
        queryset = queryset.filter(*core.filter_validity())
        return queryset
    

   @classmethod
   def get_queryset(cls, queryset, user):
        queryset = cls.filter_queryset(queryset)
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=None)
        if settings.ROW_SECURITY:
            pass
        return queryset
   
#Ticket models


class Ticket(core_models.VersionedModel,):
   
    id = models.AutoField(db_column='TicketId', primary_key=True)
    uuid = models.CharField(db_column='TicketUUID', max_length=36, default=uuid.uuid4, unique=True)
    ticket_title = models.CharField(db_column='TicketTitle', max_length= 255, blank= True, null= True )
    ticket_code = models.CharField(db_column='TicketCode', max_length=16, unique=True, blank=True, null= True)
    ticket_description = models.TextField(db_column='Description', max_length= 255, blank= True, null = True )
    category = models.ForeignKey(Category, models.DO_NOTHING, db_column= 'CategoryID', blank=True, null = True, related_name="tickets")
    insuree = models.ForeignKey(insuree_models.Insuree, on_delete= models.DO_NOTHING, db_column='InsureeID', blank = True, null = True, related_name="tickets" )
    name = models.CharField(db_column= "Name", max_length= 100, blank= True, null= True )
    phone = models.CharField(db_column='PhoneNumber', max_length= 25, blank=True, null=True)
    email = models.CharField(db_column="Email", max_length= 200, blank= True, null= True)
    date_of_incident = models.DateField(db_column= "Date_of_Incident", blank = True, null = True)
    name_of_complainant = models.CharField(db_column= "Name of Complainanat", max_length= 100, blank = True, null = True)
    witness = models.CharField(db_column= "Witness", max_length= 255, blank = True, null = True)
    # location = models.ForeignKey(location_models.Location, on_delete= models.DO_NOTHING, db_column='LocationId', blank = True, null = True, related_name="tickets" )
    resolution = models.CharField(db_column= "Resolution", max_length= 255, blank = True, null = True)
    ticket_status = models.CharField( db_column='TicketStatus', max_length= 20, blank = True, null = True)
    ticket_priority = models.CharField(db_column='TicketPriority', max_length= 20, blank = True, null = True)
    ticket_dueDate = models.DateField(db_column= "Tciket_DueDate", blank = True, null = True)

    date_submitted = fields.DateField(db_column= "Date_Submission", blank= True, default= py_datetime.now)



    def __str__(self):
        return f"{self.ticket_title}"

    class Meta:
        managed = True
        db_table = 'tblTicket'

    
    @classmethod
    def filter_queryset(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all() 
        queryset = queryset.filter(*core.filter_validity())
        return queryset

    @classmethod
    def get_queryset(cls, queryset, user):
        queryset = cls.filter_queryset(queryset)
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=None)
        if settings.ROW_SECURITY:
            pass
        return queryset
    

# Ticket Attachmnet Module

class TicketAttachment (core_models.UUIDModel, core_models.UUIDVersionedModel,):

   uuid = models.CharField(db_column='AttachmentUUID', max_length=36, default=uuid.uuid4, unique=True)
   ticket = models.ForeignKey(
        Ticket, models.DO_NOTHING, related_name='attachment', db_column= 'TicketId', blank= True, null = True)
   filename = models.TextField(max_length = 1000, blank=True, null=True)
   mime_type = models.TextField(max_length = 255, blank=True, null=True)
   url = models.TextField(max_length = 1000, blank=True, null=True)
   document = models.TextField(blank=True, null=True)
   date = fields.DateField(blank=True, default=py_datetime.now)
   
   def __str__(self):
        return f"{self.filename}"
   
   def full_file_path(self):
        if not TicketConfig.tickets_attachments_root_path or not self.filename:
            return None
        return os.path.join(TicketConfig.tickets_attachments_root_path,  self.filename)

   

   class Meta:
        managed = True
        db_table = 'tblTicketAttachment'
    
   @classmethod
   def filter_queryset(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all() 
        queryset = queryset.filter(*core.filter_validity())
        return queryset

   @classmethod
   def get_queryset(cls, queryset, user):
        queryset = cls.filter_queryset(queryset)
        if isinstance(user, ResolveInfo):
            user = user.context.user
        if settings.ROW_SECURITY and user.is_anonymous:
            return queryset.filter(id=None)
        if settings.ROW_SECURITY:
            pass
        return queryset



class TicketMutation(core_models.UUIDModel, core_models.ObjectMutation):
    ticket = models.ForeignKey(Ticket, models.DO_NOTHING,
                              related_name='mutations')
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name='tickets')
 
    class Meta:
        managed = True
        db_table = "ticket_TicketMutation"


class CategoryMutation(core_models.UUIDModel, core_models.ObjectMutation):
    category  = models.ForeignKey(Category, models.DO_NOTHING,
                              related_name='mutations')
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name='category')

    class Meta:
        managed = True
        db_table = "ticket_CategoryMutation"

class AttachmentMutation(core_models.UUIDModel, core_models.ObjectMutation):
    ticket = models.ForeignKey(TicketAttachment, models.DO_NOTHING,
                              related_name='mutations')
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name='attachment')
 
    class Meta:
        managed = True
        db_table = "ticket_AttachmentMutation"
        