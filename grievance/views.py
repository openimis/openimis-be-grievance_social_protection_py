import core
import base64
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render
from .models import TicketAttachment
from django.utils.translation import gettext as _
from .apps import TicketConfig
# Create your views here.

def attach(request):
    queryset = TicketAttachment.objects.filter(*core.filter_validity())
    attachment = queryset\
        .filter(id=request.GET['id'])\
        .first()
    if not attachment:
        raise PermissionDenied(_("unauthorized"))

    if TicketConfig.tickets_attachments_root_path and attachment.url is None:
        response = HttpResponse(status=404)
        return response

    if not TicketConfig.tickets_attachments_root_path and attachment.document is None:
        response = HttpResponse(status=404)
        return response

    response = HttpResponse(content_type=("application/x-binary" if attachment.mime_type is None else attachment.mime_type))
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.filename
    if TicketConfig.tickets_attachments_root_path:
        f = open('%s/%s' % (TicketConfig.tickets_attachments_root_path, attachment.url), "rb")
        response.write(f.read())
        f.close()
    else:
        response.write(base64.b64decode(attachment.document))
    return response

