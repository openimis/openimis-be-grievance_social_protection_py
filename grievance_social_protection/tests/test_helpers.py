from grievance_social_protection.models import (
    Comment,
    Ticket
)
from grievance_social_protection.tests.data import service_add_ticket_payload


def create_ticket(user):
    ticket = Ticket(**service_add_ticket_payload)
    ticket.save(user=user)
    return ticket


def create_comment_for_existing_ticket(user, ticket, resolved=False):
    comment = Comment(**{
        "ticket_id": ticket.id,
        "comment": "awesome comment",
        "is_resolution": True if resolved else False
    })
    comment.save(user=user)
    if resolved:
        ticket.status = 'CLOSED'
        ticket.save(user=user)
    return comment
