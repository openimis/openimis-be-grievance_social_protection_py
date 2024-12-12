from grievance_social_protection.models import (
    Comment,
    Ticket
)
from grievance_social_protection.tests.data import service_add_ticket_payload


def create_ticket(username):
    ticket = Ticket(**service_add_ticket_payload)
    ticket.save(username=username)
    return ticket


def create_comment_for_existing_ticket(user, ticket):
    comment = Comment({
        "ticket_id": ticket.id,
        "comment": "awesome comment"
    })
    comment.save(user=user)
    return comment
