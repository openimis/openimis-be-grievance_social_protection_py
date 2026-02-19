from django.test import TestCase

from core.test_helpers import create_test_interactive_user
from grievance_social_protection.apps import TicketConfig
from grievance_social_protection.models import Ticket
from grievance_social_protection.tests.test_helpers import (
    setup_grievance_config, assign_rights_to_user, get_rights, collect_all_rights,
)


class TicketQueryFilteringTest(TestCase):
    """Test ticket queryset filtering based on permissions"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_test_config()
        cls._create_test_users()
        cls._create_test_tickets()

    def setUp(self):
        # Reset config for each test
        self._setup_test_config()

    @classmethod
    def _setup_test_config(cls):
        """Set up test configuration"""
        cfg = {
            'grievance_types': [
                'public_category',
                {
                    'name': 'restricted_category',
                    'permissions': ['restricted_read', 'read', 'create']
                },
                {
                    'name': 'sensitive_category',
                    'permissions': ['restricted_read', 'read'],
                    'default_flags': ['sensitive']
                }
            ],
            'grievance_flags': [
                'urgent',
                {
                    'name': 'sensitive',
                    'permissions': ['restricted_read', 'read', 'create']
                },
                {
                    'name': 'confidential',
                    'permissions': ['restricted_read', 'read']
                }
            ]
        }
        setup_grievance_config(cfg)

    @classmethod
    def _create_test_users(cls):
        """Create test users with different permission levels"""
        # User with all permissions
        cls.user_all_perms = create_test_interactive_user(username='user_all_perms', roles=[7])
        all_right_ids = [127000] + list(collect_all_rights())
        assign_rights_to_user(cls.user_all_perms, all_right_ids, 'QFAllPermsRole')

        # User with limited permissions (only basic query permission)
        cls.user_limited = create_test_interactive_user(username='user_limited', roles=[1])
        assign_rights_to_user(cls.user_limited, [127000], 'QFLimitedRole')

        # User with mixed permissions - can read sensitive flag
        cls.user_mixed = create_test_interactive_user(username='user_mixed', roles=[1])
        sensitive_rights = get_rights('processed_flags', 'sensitive')
        mixed_ids = [127000]
        if sensitive_rights.get('read'):
            mixed_ids.append(sensitive_rights['read'])
        assign_rights_to_user(cls.user_mixed, mixed_ids, 'QFMixedRole')

    @classmethod
    def _create_test_tickets(cls):
        """Create test tickets"""
        cls.tickets = {}

        ticket = Ticket(
            title='Public ticket',
            category='public_category',
            flags='urgent',
            resolution='5,0'
        )
        ticket.save(user=cls.user_all_perms)
        cls.tickets['public'] = ticket

        ticket = Ticket(
            title='Restricted ticket',
            category='restricted_category',
            flags='urgent',
            resolution='5,0'
        )
        ticket.save(user=cls.user_all_perms)
        cls.tickets['restricted'] = ticket

        ticket = Ticket(
            title='Sensitive ticket',
            category='sensitive_category',
            flags='sensitive',
            resolution='5,0'
        )
        ticket.save(user=cls.user_all_perms)
        cls.tickets['sensitive'] = ticket

        ticket = Ticket(
            title='Public with confidential flag',
            category='public_category',
            flags='confidential',
            resolution='5,0'
        )
        ticket.save(user=cls.user_all_perms)
        cls.tickets['confidential'] = ticket

    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        ticket_ids = [t.id for t in cls.tickets.values()]
        Ticket.objects.filter(id__in=ticket_ids).delete()
        super().tearDownClass()

    def test_filter_all_permissions(self):
        """Test filtering with all permissions"""
        test_ticket_ids = [t.id for t in self.tickets.values()]
        queryset = Ticket.objects.filter(id__in=test_ticket_ids)

        filtered = Ticket.get_queryset(queryset, self.user_all_perms)

        ticket_ids = list(filtered.values_list('id', flat=True))

        for name, ticket in self.tickets.items():
            self.assertIn(ticket.id, ticket_ids,
                         f"Admin user should see '{name}' ticket (category={ticket.category}, flags={ticket.flags})")

    def test_filter_limited_permissions(self):
        """Test filtering with limited permissions"""
        queryset = Ticket.objects.all()
        filtered = Ticket.get_queryset(queryset, self.user_limited)

        ticket_ids = list(filtered.values_list('id', flat=True))

        self.assertIn(self.tickets['public'].id, ticket_ids)
        self.assertNotIn(self.tickets['restricted'].id, ticket_ids)
        self.assertNotIn(self.tickets['sensitive'].id, ticket_ids)
        self.assertNotIn(self.tickets['confidential'].id, ticket_ids)

    def test_filter_no_config(self):
        """Test filtering when no config exists"""
        original_cats = TicketConfig.processed_categories
        original_flags = TicketConfig.processed_flags
        TicketConfig.processed_categories = {}
        TicketConfig.processed_flags = {}

        try:
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.user_limited)
            self.assertEqual(queryset.count(), filtered.count())
        finally:
            TicketConfig.processed_categories = original_cats
            TicketConfig.processed_flags = original_flags

    def test_filter_mixed_flags(self):
        """Test filtering with mixed flag permissions"""
        mixed_ticket = Ticket(
            title='Mixed flags',
            category='public_category',
            flags='urgent sensitive',
            resolution='5,0'
        )
        mixed_ticket.save(user=self.user_mixed)

        try:
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.user_mixed)

            ticket_ids = list(filtered.values_list('id', flat=True))
            self.assertIn(mixed_ticket.id, ticket_ids)
            self.assertNotIn(self.tickets['confidential'].id, ticket_ids)
        finally:
            mixed_ticket.delete(username=self.user_mixed.username)

    def test_filter_hierarchical_categories(self):
        """Test filtering with hierarchical categories"""
        cfg = {
            'grievance_types': [
                'public_category',
                {
                    'name': 'parent',
                    'permissions': ['read', 'create'],
                    'children': ['child1', 'child2']
                }
            ],
            'grievance_flags': ['urgent']
        }
        setup_grievance_config(cfg)

        parent_ticket = Ticket(title='Parent', category='parent', resolution='5,0')
        parent_ticket.save(user=self.user_limited)
        child_ticket = Ticket(title='Child', category='parent|child1', resolution='5,0')
        child_ticket.save(user=self.user_limited)

        try:
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.user_limited)

            ticket_ids = list(filtered.values_list('id', flat=True))
            self.assertNotIn(parent_ticket.id, ticket_ids)
            self.assertNotIn(child_ticket.id, ticket_ids)
        finally:
            parent_ticket.delete(username=self.user_limited.username)
            child_ticket.delete(username=self.user_limited.username)
