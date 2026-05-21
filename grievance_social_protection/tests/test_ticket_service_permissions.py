from django.core.exceptions import ValidationError
from django.test import TestCase

from core.test_helpers import LogInHelper, create_test_interactive_user
from grievance_social_protection.services import TicketService
from grievance_social_protection.models import Ticket
from grievance_social_protection.tests.test_helpers import (
    setup_grievance_config, restore_grievance_config,
    assign_rights_to_user, get_rights,
)


class TicketServicePermissionsTest(TestCase):
    """Test permission-based access control in TicketService"""

    _config_snapshot = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._config_snapshot = cls._setup_test_config()
        cls._create_test_users()

    @classmethod
    def tearDownClass(cls):
        if cls._config_snapshot:
            restore_grievance_config(cls._config_snapshot)
        super().tearDownClass()

    def setUp(self):
        self._per_test_snapshot = self._setup_test_config()

    def tearDown(self):
        restore_grievance_config(self._per_test_snapshot)

    @classmethod
    def _setup_test_config(cls):
        """Set up test configuration, returns snapshot for restore."""
        cfg = {
            'grievance_types': [
                'open_category',
                {
                    'name': 'restricted_category',
                    'priority': 'High',
                    'permissions': ['read', 'create'],
                    'default_flags': ['urgent']
                }
            ],
            'grievance_flags': [
                'public',
                {
                    'name': 'sensitive',
                    'priority': 'Critical',
                    'permissions': ['read', 'create']
                },
                {
                    'name': 'urgent',
                    'priority': 'High'
                }
            ],
            'resolution_times': '5,0'
        }
        return setup_grievance_config(cfg)

    @classmethod
    def _create_test_users(cls):
        """Create test users with different permission levels"""
        # User with permissions for restricted category
        cls.user_with_perms = create_test_interactive_user(username='user_with_perms', roles=[1])
        cat_rights = get_rights('processed_categories', 'restricted_category')
        perms = []
        if cat_rights.get('read'):
            perms.append(cat_rights['read'])
        if cat_rights.get('create'):
            perms.append(cat_rights['create'])
        assign_rights_to_user(cls.user_with_perms, perms, 'SPWithPermsRole')

        # User without permissions
        cls.user_no_perms = create_test_interactive_user(username='user_no_perms', roles=[1])

        # User with flag permissions
        cls.user_flag_perms = create_test_interactive_user(username='user_flag_perms', roles=[1])
        flag_rights = get_rights('processed_flags', 'sensitive')
        flag_perms = []
        if flag_rights.get('read'):
            flag_perms.append(flag_rights['read'])
        if flag_rights.get('create'):
            flag_perms.append(flag_rights['create'])
        assign_rights_to_user(cls.user_flag_perms, flag_perms, 'SPFlagPermsRole')

        # Anonymous-like user (no permissions)
        cls.user_anon = create_test_interactive_user(username='user_anon', roles=[1])

    def test_create_with_permissions_allowed(self):
        """Test ticket creation when user has required permissions"""
        service = TicketService(self.user_with_perms)

        obj_data = {
            'category': 'restricted_category',
            'title': 'Test with permissions',
            'resolution': '5,0'
        }

        result = service.create(obj_data)

        self.assertTrue(result.get('success', False), f"Creation failed: {result}")
        self.assertIsNotNone(result.get('data', {}).get('uuid'))

        ticket = Ticket.objects.get(uuid=result['data']['uuid'])
        self.assertEqual(ticket.category, 'restricted_category')
        self.assertEqual(ticket.flags, 'urgent')  # Default flag applied
        self.assertEqual(ticket.priority, 'High')  # Category priority

        ticket.delete(username=self.user_with_perms.username)

    def test_create_with_permissions_denied(self):
        """Test ticket creation fails when user lacks permissions"""
        service = TicketService(self.user_no_perms)

        obj_data = {
            'category': 'restricted_category',
            'title': 'Test without permissions',
            'resolution': '5,0'
        }

        with self.assertRaises(ValidationError) as cm:
            service.create(obj_data)

        self.assertIn('restricted_category', str(cm.exception))

    def test_flag_permissions(self):
        """Test flag permission checking"""
        service = TicketService(self.user_no_perms)

        obj_data = {
            'category': 'open_category',
            'title': 'Test flag permissions',
            'flags': 'public sensitive',
            'resolution': '5,0'
        }

        with self.assertRaises(ValidationError) as cm:
            service.create(obj_data)

        self.assertIn('sensitive', str(cm.exception))

        # User with flag permissions should succeed
        service_with_flag_perms = TicketService(self.user_flag_perms)
        result = service_with_flag_perms.create(obj_data)

        self.assertTrue(result.get('success', False))
        if result.get('success'):
            ticket = Ticket.objects.get(uuid=result['data']['uuid'])
            self.assertIn('sensitive', ticket.flags)
            ticket.delete(username=self.user_flag_perms.username)

    def test_open_category_no_permissions_required(self):
        """Test that open categories don't require permissions"""
        service = TicketService(self.user_no_perms)

        obj_data = {
            'category': 'open_category',
            'title': 'Test open category',
            'resolution': '5,0'
        }

        result = service.create(obj_data)
        self.assertTrue(result.get('success', False), f"Creation failed: {result}")

        if result.get('success'):
            ticket = Ticket.objects.get(uuid=result['data']['uuid'])
            ticket.delete(username=self.user_no_perms.username)

    def test_anonymous_user_behavior(self):
        """Test behavior with user having no permissions"""
        class AnonymousLikeUser:
            def __init__(self, base_user):
                self.base_user = base_user
                self.is_anonymous = True

            def __getattr__(self, name):
                return getattr(self.base_user, name)

        anon_user = AnonymousLikeUser(self.user_anon)
        service = TicketService(anon_user)

        obj_data = {
            'category': 'open_category',
            'title': 'Test anonymous',
            'resolution': '5,0'
        }

        with self.assertRaises(ValidationError) as cm:
            service.create(obj_data)

        error_str = str(cm.exception).lower()
        self.assertTrue('authentication' in error_str or 'permission' in error_str)

    def test_category_defaults_applied(self):
        """Test that category defaults are applied correctly"""
        user = LogInHelper().get_or_create_user_api()
        service = TicketService(user)

        cat_rights = get_rights('processed_categories', 'restricted_category')
        perms = []
        if cat_rights.get('read'):
            perms.append(cat_rights['read'])
        if cat_rights.get('create'):
            perms.append(cat_rights['create'])
        assign_rights_to_user(user, perms, 'SPDefaultsRole')

        obj_data = {
            'category': 'restricted_category',
            'title': 'Test defaults',
            'resolution': '5,0'
        }

        result = service.create(obj_data)

        if result.get('success'):
            ticket = Ticket.objects.get(uuid=result['data']['uuid'])
            self.assertEqual(ticket.priority, 'High')
            self.assertEqual(ticket.flags, 'urgent')
            ticket.delete(username=user.username)

    def test_permission_inheritance(self):
        """Test that child categories inherit parent permissions"""
        cfg = {
            'grievance_types': [
                'open_category',
                {
                    'name': 'parent_cat',
                    'permissions': ['read', 'create'],
                    'children': ['child1', 'child2']
                }
            ],
            'grievance_flags': ['urgent'],
            'resolution_times': '5,0'
        }
        setup_grievance_config(cfg)

        service = TicketService(self.user_no_perms)

        obj_data = {
            'category': 'parent_cat > child1',
            'title': 'Test child category',
            'resolution': '5,0'
        }

        with self.assertRaises(ValidationError) as cm:
            service.create(obj_data)

        self.assertIn('parent_cat > child1', str(cm.exception))
