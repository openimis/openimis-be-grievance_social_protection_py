from grievance_social_protection.models import Ticket
from grievance_social_protection.tests.data import service_add_ticket_payload


def create_ticket(username):
    ticket = Ticket(**service_add_ticket_payload)
    ticket.save(username=username)
    return ticket
