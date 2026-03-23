from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from core.test_helpers import create_test_interactive_user

from grievance_social_protection.access_control import GrievanceAccessControl
from grievance_social_protection.apps import TicketConfig
from grievance_social_protection.models import Ticket
from grievance_social_protection.rights import GrievanceRightsManager
from grievance_social_protection.tests.test_helpers import (
    setup_grievance_config, assign_rights_to_user, get_rights, collect_all_rights,
)
import grievance_social_protection


class GrievanceAccessControlTest(TestCase):
    """Test automatic rights generation and access control for grievance categories and flags"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_with_all_rights = create_test_interactive_user(username='user_all_rights', roles=[1])
        cls.user_no_rights = create_test_interactive_user(username='user_no_rights', roles=[1])
        cls.user_restricted_viewer = create_test_interactive_user(username='user_restricted', roles=[1])
        cls.user_full_viewer = create_test_interactive_user(username='user_viewer', roles=[1])
        cls.user_manager = create_test_interactive_user(username='user_manager', roles=[1])

    def setUp(self):
        """Set up test configuration before each test"""
        self._setup_test_config()
        self._assign_rights_to_users()

    def _setup_test_config(self):
        """Set up test configuration data with new permissions format"""
        cfg = {
            'grievance_types': [
                'simple_category',
                {
                    'name': 'complaint',
                    'priority': 'High',
                    'permissions': ['restricted_read', 'read', 'create', 'update'],
                    'default_flags': ['urgent'],
                    'children': [
                        {
                            'name': 'service_complaint',
                            'permissions': ['read', 'create']
                        },
                        {
                            'name': 'vbg_complaint',
                            'permissions': ['read', 'create'],
                            'default_flags': ['confidential']
                        }
                    ]
                },
                {
                    'name': 'feedback',
                    'priority': 'Low',
                    'permissions': ['restricted_read', 'read']
                },
                {
                    'name': 'restricted_category',
                    'priority': 'Critical',
                    'permissions': ['read', 'create', 'update'],
                    'default_flags': ['sensitive']
                }
            ],
            'grievance_flags': [
                {
                    'name': 'urgent',
                    'priority': 'High'
                },
                {
                    'name': 'confidential',
                    'priority': 'Critical',
                    'permissions': ['read', 'create']
                },
                {
                    'name': 'sensitive',
                    'priority': 'Critical',
                    'permissions': ['read']
                },
                'public'
            ]
        }
        setup_grievance_config(cfg)

    def _assign_rights_to_users(self):
        """Assign specific rights to test users through roles"""
        complaint_rights = get_rights('processed_categories', 'complaint')

        # Restricted viewer - only restricted_read for complaint
        if complaint_rights.get('restricted_read'):
            assign_rights_to_user(
                self.user_restricted_viewer,
                [complaint_rights['restricted_read']],
                'ACRestrictedViewer',
            )

        # Full viewer - read for complaint
        if complaint_rights.get('read'):
            assign_rights_to_user(
                self.user_full_viewer,
                [complaint_rights['read']],
                'ACViewer',
            )

        # Manager - all complaint rights
        assign_rights_to_user(
            self.user_manager,
            list(complaint_rights.values()),
            'ACManager',
        )

        # User with all rights across all categories and flags
        all_right_ids = list(collect_all_rights())
        assign_rights_to_user(
            self.user_with_all_rights,
            all_right_ids,
            'ACAllRights',
        )

    def test_automatic_rights_generation(self):
        """Test that rights are generated for categories with permissions"""
        complaint_info = TicketConfig.processed_categories.get('complaint', {})
        self.assertIn('generated_rights', complaint_info)
        self.assertIn('restricted_read', complaint_info['generated_rights'])
        self.assertIn('read', complaint_info['generated_rights'])
        self.assertIn('create', complaint_info['generated_rights'])
        self.assertIn('update', complaint_info['generated_rights'])

        feedback_info = TicketConfig.processed_categories.get('feedback', {})
        self.assertIn('generated_rights', feedback_info)
        self.assertIn('restricted_read', feedback_info['generated_rights'])
        self.assertIn('read', feedback_info['generated_rights'])
        self.assertNotIn('create', feedback_info['generated_rights'])
        self.assertNotIn('update', feedback_info['generated_rights'])

    def test_check_category_access_with_new_permissions(self):
        """Test category access with new permission system using real rights"""
        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_restricted_viewer, 'complaint', 'restricted_read'
            )
        )
        self.assertFalse(
            GrievanceAccessControl.check_category_access(
                self.user_restricted_viewer, 'complaint', 'read'
            )
        )

        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_full_viewer, 'complaint', 'read'
            )
        )
        self.assertFalse(
            GrievanceAccessControl.check_category_access(
                self.user_full_viewer, 'complaint', 'create'
            )
        )

        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_manager, 'complaint', 'create'
            )
        )
        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_manager, 'complaint', 'update'
            )
        )

    def test_get_user_access_level(self):
        """Test determining user's access level with real database rights"""
        level = GrievanceAccessControl.get_user_access_level(
            self.user_restricted_viewer, 'complaint'
        )
        self.assertEqual(level, 'restricted')

        level = GrievanceAccessControl.get_user_access_level(
            self.user_full_viewer, 'complaint'
        )
        self.assertEqual(level, 'read')

        level = GrievanceAccessControl.get_user_access_level(
            self.user_manager, 'complaint'
        )
        self.assertEqual(level, 'full')

        level = GrievanceAccessControl.get_user_access_level(
            self.user_no_rights, 'complaint'
        )
        self.assertEqual(level, 'none')

        level = GrievanceAccessControl.get_user_access_level(
            self.user_no_rights, 'simple_category'
        )
        self.assertEqual(level, 'full')

    def test_validate_ticket_access_new_system(self):
        """Test ticket access validation with new permission system"""
        try:
            GrievanceAccessControl.validate_ticket_access(
                self.user_manager, 'complaint', None, 'create'
            )
        except PermissionDenied:
            self.fail("validate_ticket_access raised PermissionDenied unexpectedly")

        with self.assertRaises(PermissionDenied) as context:
            GrievanceAccessControl.validate_ticket_access(
                self.user_full_viewer, 'complaint', None, 'create'
            )
        self.assertIn('create', str(context.exception))

    def test_get_user_rights(self):
        """Test getting user rights from database"""
        manager_rights = set(self.user_manager.rights) if self.user_manager.rights else set()
        complaint_rights = get_rights('processed_categories', 'complaint')

        for right_id in complaint_rights.values():
            self.assertIn(right_id, manager_rights)

        no_rights = set(self.user_no_rights.rights) if self.user_no_rights.rights else set()
        for right_id in complaint_rights.values():
            self.assertNotIn(right_id, no_rights)

    def test_permission_inheritance_with_overrides(self):
        """Test that child categories can override parent permissions"""
        service_info = TicketConfig.processed_categories.get('complaint|service_complaint', {})
        rights = service_info.get('generated_rights', {})

        self.assertIn('read', rights)
        self.assertIn('create', rights)
        self.assertNotIn('update', rights)

    def test_get_accessible_categories_with_min_access(self):
        """Test getting accessible categories with minimum access level"""
        categories = GrievanceAccessControl.get_accessible_categories(
            self.user_restricted_viewer
        )
        self.assertIn('complaint', categories)

    def test_empty_permissions_means_no_restrictions(self):
        """Test that categories/flags without permissions have no access restrictions"""
        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_no_rights, 'simple_category', 'read'
            )
        )

        self.assertTrue(
            GrievanceAccessControl.check_flag_access(
                self.user_no_rights, 'public', 'read'
            )
        )

    def test_filter_ticket_queryset(self):
        """Test filtering queryset based on user rights"""
        ticket1 = Ticket(
            category='complaint',
            title='Test Complaint',
            code='TEST001'
        )
        ticket1.save(user=self.user_manager.user)

        ticket2 = Ticket(
            category='simple_category',
            title='Test Simple',
            code='TEST002'
        )
        ticket2.save(user=self.user_manager.user)

        queryset = Ticket.objects.all()
        filtered = GrievanceAccessControl.filter_ticket_queryset(queryset, self.user_no_rights)

        self.assertIn(ticket2, filtered)
        self.assertNotIn(ticket1, filtered)

        filtered = GrievanceAccessControl.filter_ticket_queryset(queryset, self.user_restricted_viewer)
        self.assertGreaterEqual(filtered.count(), 2)

        ticket1.delete(user=self.user_manager.user)
        ticket2.delete(user=self.user_manager.user)


class GrievanceRightsManagerTest(TestCase):
    """Test automatic rights generation functionality"""

    def test_get_next_available_id(self):
        """Test the internal ID generation logic"""
        used_ids = set()

        next_id = GrievanceRightsManager._get_next_available_id('read', used_ids)
        self.assertEqual(next_id % 10, 0)
        self.assertEqual(next_id, GrievanceRightsManager.GRIEVANCE_RIGHT_BASE + 0)

        next_id = GrievanceRightsManager._get_next_available_id('create', used_ids)
        self.assertEqual(next_id % 10, 1)
        self.assertEqual(next_id, GrievanceRightsManager.GRIEVANCE_RIGHT_BASE + 1)

        used_ids = {127100, 127101, 127102}
        next_id = GrievanceRightsManager._get_next_available_id('read', used_ids)
        self.assertEqual(next_id, 127110)

    def test_generate_automatic_rights_integration(self):
        """Test the actual rights generation process"""
        app_config = TicketConfig('grievance_social_protection', grievance_social_protection)

        app_config.processed_categories = {
            'test_category': {
                'permissions': ['read', 'create', 'update']
            }
        }
        app_config.processed_flags = {
            'test_flag': {
                'permissions': ['read']
            }
        }

        ct = ContentType.objects.get_for_model(Ticket)
        perms_before = Permission.objects.filter(
            content_type=ct,
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).count()

        GrievanceRightsManager.generate_automatic_rights(app_config)

        perms_after = Permission.objects.filter(
            content_type=ct,
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).count()

        self.assertGreaterEqual(perms_after, perms_before)

        self.assertIn('generated_rights', app_config.processed_categories['test_category'])
        self.assertIn('generated_rights', app_config.processed_flags['test_flag'])

        Permission.objects.filter(
            content_type=ct,
            codename__endswith='_grievance',
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).delete()
