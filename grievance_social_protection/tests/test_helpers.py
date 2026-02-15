from core.test_helpers import create_test_interactive_user, create_test_role
from grievance_social_protection.models import (
    Comment,
    Ticket
)
from grievance_social_protection.tests.data import service_add_ticket_payload


def create_test_grievance_user(username='user_authorized'):
    perm_names = [
        "gql_query_tickets_perms",
        "gql_query_comments_perms",
        "gql_mutation_create_tickets_perms",
        "gql_mutation_update_tickets_perms",
        "gql_mutation_delete_tickets_perms",
        "gql_mutation_create_comment_perms",
        "gql_mutation_resolve_grievance_perms",
    ]
    role = create_test_role(perm_names=perm_names, name="GrievanceUserRole")
    return create_test_interactive_user(username=username, roles=[role.id])


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
