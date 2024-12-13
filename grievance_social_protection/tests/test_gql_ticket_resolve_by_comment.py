from django.test import TestCase
from core.models import MutationLog
from graphene import Schema
from graphene.test import Client
from core.test_helpers import create_test_interactive_user
from grievance_social_protection.schema import Query, Mutation
from grievance_social_protection.tests.gql_payloads import gql_mutation_resolve_ticket_by_comment
from grievance_social_protection.tests.test_helpers import (
    create_ticket,
    create_comment_for_existing_ticket
)


class GQLTicketResolveByCommentTestCase(TestCase):
    class GQLContext:
        def __init__(self, user):
            self.user = user

    user = None

    existing_ticket = None
    existing_comment = None
    status = "CLOSED"

    @classmethod
    def setUpClass(cls):
        super(GQLTicketResolveByCommentTestCase, cls).setUpClass()
        cls.user = create_test_interactive_user(username='user_authorized', roles=[7])
        cls.existing_ticket = create_ticket(cls.user.username)
        cls.existing_comment = create_comment_for_existing_ticket(cls.user, cls.existing_ticket)

        gql_schema = Schema(
            query=Query,
            mutation=Mutation
        )

        cls.gql_client = Client(gql_schema)
        cls.gql_context = cls.GQLContext(cls.user)

    def test_resolve_ticket_by_comment_success(self):
        mutation_id = "99g154h5b92h11sd33"
        payload = gql_mutation_resolve_ticket_by_comment % (
            self.existing_comment.id,
            mutation_id
        )

        _ = self.gql_client.execute(payload, context=self.gql_context)
        mutation_log = MutationLog.objects.get(client_mutation_id=mutation_id)
        self.assertFalse(mutation_log.error)
        self.assertEquals(self.existing_comment.is_resolution, True)
        self.assertEquals(self.existing_ticket.status, self.status)
