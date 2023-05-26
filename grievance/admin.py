from django.contrib import admin
# Register your models here.
from .models import Ticket,Category,TicketAttachment

admin.site.register(Ticket)
admin.site.register(TicketAttachment)
admin.site.register(Category)

