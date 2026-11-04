"""Comments need the comment right; attending a ticket grants nothing by itself (audit C5)."""

from uuid import uuid4

from graphene import Schema
from graphene.test import Client
from graphql_relay import to_global_id

from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from core.test_helpers import create_test_interactive_user
from grievance_social_protection.models import Comment, Ticket
from grievance_social_protection.schema import Query, Mutation
from grievance_social_protection.tests.data import service_add_ticket_payload
from grievance_social_protection.tests.gql_payloads import gql_mutation_create_comment_anonymous_user
from grievance_social_protection.tests.test_helpers import (
    create_comment_for_existing_ticket,
    create_test_grievance_user,
)

COMMENTS_QUERY = """
query { comments { edges { node { comment ticket { id } } } } }
"""


class CommentRowSecurityTestCase(openIMISGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.right_holder = create_test_grievance_user(username="c5_right_holder")
        # Attends ticket A but holds no grievance right.
        cls.staff = create_test_interactive_user(username="c5_staff", roles=[])

        cls.ticket_a = Ticket(**{**service_add_ticket_payload, "code": "C5-TICKET-A"}, attending_staff=cls.staff)
        cls.ticket_a.save(user=cls.right_holder)
        cls.ticket_b = Ticket(**{**service_add_ticket_payload, "code": "C5-TICKET-B"})
        cls.ticket_b.save(user=cls.right_holder)
        create_comment_for_existing_ticket(cls.right_holder, cls.ticket_a)
        create_comment_for_existing_ticket(cls.right_holder, cls.ticket_b)

        cls.gql_client = Client(Schema(query=Query, mutation=Mutation))

    @staticmethod
    def _gid(ticket):
        return to_global_id("TicketGQLType", ticket.id)

    def _ticket_ids(self, user):
        output = self.gql_client.execute(COMMENTS_QUERY, context=BaseTestContext(user).get_request())
        self.assertIsNone(output.get("errors"))
        edges = output["data"]["comments"]["edges"]
        return {e["node"]["ticket"]["id"] for e in edges} & {self._gid(self.ticket_a), self._gid(self.ticket_b)}

    def _comment_on(self, user, ticket):
        before = Comment.objects.filter(ticket=ticket).count()
        payload = gql_mutation_create_comment_anonymous_user % ("c5 comment", ticket.id, str(uuid4()))
        self.gql_client.execute(payload, context=BaseTestContext(user).get_request())
        return Comment.objects.filter(ticket=ticket).count() > before

    def test_right_holder_reads_visible_ticket_comments(self):
        self.assertEqual(self._ticket_ids(self.right_holder), {self._gid(self.ticket_a), self._gid(self.ticket_b)})

    def test_attending_staff_without_right_cannot_read(self):
        output = self.gql_client.execute(COMMENTS_QUERY, context=BaseTestContext(self.staff).get_request())
        self.assertTrue(output.get("errors"))

    def test_attending_staff_without_right_cannot_comment(self):
        self.assertFalse(self._comment_on(self.staff, self.ticket_a))
        self.assertFalse(self._comment_on(self.staff, self.ticket_b))

    def test_right_holder_can_comment(self):
        self.assertTrue(self._comment_on(self.right_holder, self.ticket_b))
