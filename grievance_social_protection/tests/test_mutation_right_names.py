"""
Each grievance mutation must check the right that matches what it does.

`CreateCommentMutation` checked `gql_mutation_delete_tickets_perms` (127003) while the
purpose built `gql_mutation_create_comment_perms` (127005) - declared from the start,
and granted to imis_admin by migration 0014 - was never checked anywhere. The only way
to earn commenting was therefore to hold the ticket *delete* right.
"""

import ast
import inspect
import re

from django.test import TestCase

from grievance_social_protection import gql_mutations
from grievance_social_protection.apps import TicketConfig

EXPECTED_PERMS = {
    "CreateTicketMutation": {"gql_mutation_create_tickets_perms"},
    "UpdateTicketMutation": {"gql_mutation_update_tickets_perms"},
    "DeleteTicketMutation": {"gql_mutation_delete_tickets_perms"},
    "CreateCommentMutation": {"gql_mutation_create_comment_perms"},
    "ResolveGrievanceByCommentMutation": {"gql_mutation_resolve_grievance_perms"},
    "ReopenTicketMutation": {"gql_mutation_update_tickets_perms"},
}

PERM_REF = re.compile(r"TicketConfig\.(\w*perms\w*)")


def _perms_referenced(class_name):
    source = inspect.getsource(getattr(gql_mutations, class_name))
    # unparse drops comments: a commented-out check must not count as a check
    return set(PERM_REF.findall(ast.unparse(ast.parse(source))))


class GrievanceMutationRightNameTestCase(TestCase):
    def test_every_mutation_checks_the_expected_right(self):
        for class_name, expected in EXPECTED_PERMS.items():
            with self.subTest(mutation=class_name):
                self.assertEqual(_perms_referenced(class_name), expected)

    def test_creating_a_comment_does_not_require_the_ticket_delete_right(self):
        self.assertNotIn(
            "gql_mutation_delete_tickets_perms",
            _perms_referenced("CreateCommentMutation"),
        )

    def test_comment_and_ticket_delete_are_distinct_rights(self):
        self.assertNotEqual(
            TicketConfig.gql_mutation_create_comment_perms,
            TicketConfig.gql_mutation_delete_tickets_perms,
        )

    def test_the_dedicated_comment_right_is_actually_checked(self):
        """It existed and was granted, but nothing read it."""
        self.assertTrue(TicketConfig.gql_mutation_create_comment_perms)
        self.assertIn(
            "gql_mutation_create_comment_perms",
            _perms_referenced("CreateCommentMutation"),
        )
