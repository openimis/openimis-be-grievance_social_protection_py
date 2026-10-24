import importlib

from django.apps import apps
from django.test import TestCase

from grievance_social_protection.access_control import GrievanceAccessControl
from grievance_social_protection.models import Ticket
from grievance_social_protection.tests.test_helpers import (
    setup_grievance_config, restore_grievance_config, create_user_with_rights, collect_all_rights,
)


def rewrite_pipe_categories():
    migration = importlib.import_module(
        'grievance_social_protection.migrations.0019_ticket_category_separator'
    )
    migration.rewrite_pipe_categories(apps, None)


class TicketCategorySeparatorMigrationTest(TestCase):
    """
    Sub-categories were stored 'parent|child' before the separator became ' > '.
    Every category lookup compares the stored name with the configured one, so a
    legacy 'parent|child' ticket was out of every ticket list and its category's
    rights and defaults did not apply to it. The data migration rewrites it once.
    """

    def setUp(self):
        self._snapshot = setup_grievance_config({
            'grievance_types': [
                {'name': 'Health', 'permissions': ['read'], 'children': ['Nutrition']},
                # A flat category whose own name contains a pipe stays as it is.
                'Water|Sanitation',
            ],
        })
        self.user = create_user_with_rights('sep_user', [127000] + list(collect_all_rights()), 'SepRole')
        self.tickets = {}
        for key, stored in {
            'legacy': 'Health|Nutrition',
            'current': 'Health > Nutrition',
            'flat': 'Water|Sanitation',
            'unconfigured': 'Roads|Bridges',
        }.items():
            ticket = Ticket(title=key, resolution='5,0')
            ticket.save(user=self.user)
            # The stored name as an earlier version wrote it; save() would apply defaults.
            Ticket.objects.filter(id=ticket.id).update(category=stored)
            self.tickets[key] = ticket

    def tearDown(self):
        restore_grievance_config(self._snapshot)

    def category(self, key):
        # Read from the database: Ticket.objects.get() may answer from the object cache.
        return Ticket.objects.filter(id=self.tickets[key].id).values_list('category', flat=True).first()

    def listed(self):
        visible = GrievanceAccessControl.filter_ticket_queryset(Ticket.objects.all(), self.user)
        return set(visible.filter(id__in=[t.id for t in self.tickets.values()]).values_list('title', flat=True))

    def test_legacy_sub_category_is_out_of_the_ticket_list(self):
        # The defect the migration repairs.
        self.assertNotIn('legacy', self.listed())

    def test_legacy_sub_category_is_rewritten_with_the_current_separator(self):
        rewrite_pipe_categories()

        self.assertEqual(self.category('legacy'), 'Health > Nutrition')
        self.assertIn('legacy', self.listed())

    def test_names_already_current_or_configured_with_a_pipe_are_kept(self):
        rewrite_pipe_categories()

        self.assertEqual(self.category('current'), 'Health > Nutrition')
        self.assertEqual(self.category('flat'), 'Water|Sanitation')

    def test_unconfigured_pipe_name_is_rewritten_too(self):
        rewrite_pipe_categories()

        self.assertEqual(self.category('unconfigured'), 'Roads > Bridges')

    def test_rewrite_runs_once(self):
        rewrite_pipe_categories()
        rewrite_pipe_categories()

        self.assertEqual(self.category('legacy'), 'Health > Nutrition')
