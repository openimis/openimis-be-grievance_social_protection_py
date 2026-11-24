"""get_queryset honours the OP-2029 validity contract (epic OP-3317, phase 1).

Explicit validity values return the expected rows; a caller asking for
nothing gets what it got before the contract existed.
"""

from django.test import TestCase

from core.test_helpers import assert_row_filters, create_test_interactive_user, mark_deleted
from grievance_social_protection.models import Ticket


class TicketRowFiltersTest(TestCase):
    def test_ticket(self):
        user = create_test_interactive_user(username="ticketrowfilters")
        live = Ticket(title="row filters live", resolution="5,0")
        live.save(username=user.username)
        deleted = Ticket(title="row filters deleted", resolution="5,0")
        deleted.save(username=user.username)
        mark_deleted(deleted)
        assert_row_filters(
            self, Ticket, Ticket.objects.filter(id__in=[live.id, deleted.id]), user,
            live.id, deleted.id, default_hides_deleted=True,
        )
