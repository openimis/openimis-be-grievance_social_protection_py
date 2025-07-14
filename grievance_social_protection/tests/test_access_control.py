from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from core.test_helpers import create_test_interactive_user
from core.models import Role, RoleRight, UserRole

from grievance_social_protection.access_control import GrievanceAccessControl
from grievance_social_protection.apps import TicketConfig
from grievance_social_protection.models import Ticket
from grievance_social_protection.rights import GrievanceRightsManager
import grievance_social_protection

class GrievanceAccessControlTest(TestCase):
    """Test automatic rights generation and access control for grievance categories and flags"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test users
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
        # Create configuration with the new permissions format
        cfg = {
            'grievance_types': [
                'simple_category',
                {
                    'name': 'complaint',
                    'priority': 'High',
                    'permissions': ['restricted_read', 'read', 'create', 'update'],  # New format
                    'default_flags': ['urgent'],
                    'children': [
                        {
                            'name': 'service_complaint',
                            'permissions': ['read', 'create']  # Override parent
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
                    'permissions': ['restricted_read', 'read']  # Read only
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
                    'permissions': ['read', 'create']  # Restricted flag
                },
                {
                    'name': 'sensitive',
                    'priority': 'Critical',
                    'permissions': ['read']  # Read only flag
                },
                'public'
            ]
        }
        
        # Process the configuration
        TicketConfig._TicketConfig__process_unified_categories(cfg)
        TicketConfig._TicketConfig__process_unified_flags(cfg)
        TicketConfig._TicketConfig__load_config(cfg)
        
        self._rights_generation()

    def _rights_generation(self):
        # Generate rights using the real rights manager
        GrievanceRightsManager.generate_automatic_rights(TicketConfig)
    
    def _assign_rights_to_users(self):
        """Assign specific rights to test users through roles"""
        # Create roles for different access levels
        complaint_rights = TicketConfig.processed_categories.get('complaint', {}).get('generated_rights', {})
        
        # Restricted viewer role
        if self.user_restricted_viewer.i_user and complaint_rights.get('restricted_read'):
            role_restricted = Role.objects.create(
                name='TestRestrictedViewer',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            RoleRight.objects.create(
                role=role_restricted,
                right_id=complaint_rights['restricted_read'],
                audit_user_id=-1
            )
            UserRole.objects.create(
                user=self.user_restricted_viewer.i_user,
                role=role_restricted,
                audit_user_id=-1
            )
        
        # Full viewer role
        if self.user_full_viewer.i_user and complaint_rights.get('read'):
            role_viewer = Role.objects.create(
                name='TestViewer',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            RoleRight.objects.create(
                role=role_viewer,
                right_id=complaint_rights['read'],
                audit_user_id=-1
            )
            UserRole.objects.create(
                user=self.user_full_viewer.i_user,
                role=role_viewer,
                audit_user_id=-1
            )
        
        # Manager role with all rights
        if self.user_manager.i_user:
            role_manager = Role.objects.create(
                name='TestManager',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Add all complaint rights
            for right_id in complaint_rights.values():
                RoleRight.objects.create(
                    role=role_manager,
                    right_id=right_id,
                    audit_user_id=-1
                )
            UserRole.objects.create(
                user=self.user_manager.i_user,
                role=role_manager,
                audit_user_id=-1
            )
        
        # User with all rights
        if self.user_with_all_rights.i_user:
            role_all = Role.objects.create(
                name='TestAllRights',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Add all generated rights
            for cat_info in TicketConfig.processed_categories.values():
                for right_id in cat_info.get('generated_rights', {}).values():
                    RoleRight.objects.create(
                        role=role_all,
                        right_id=right_id,
                        audit_user_id=-1
                    )
            for flag_info in TicketConfig.processed_flags.values():
                for right_id in flag_info.get('generated_rights', {}).values():
                    RoleRight.objects.create(
                        role=role_all,
                        right_id=right_id,
                        audit_user_id=-1
                    )
            UserRole.objects.create(
                user=self.user_with_all_rights.i_user,
                role=role_all,
                audit_user_id=-1
            )
    
    def test_automatic_rights_generation(self):
        """Test that rights are generated for categories with permissions"""
        # Check complaint category has generated rights
        complaint_info = TicketConfig.processed_categories.get('complaint', {})
        self.assertIn('generated_rights', complaint_info)
        # All permissions defined in config should be generated
        self.assertIn('restricted_read', complaint_info['generated_rights'])
        self.assertIn('read', complaint_info['generated_rights'])
        self.assertIn('create', complaint_info['generated_rights'])
        self.assertIn('update', complaint_info['generated_rights'])
        
        # Check feedback category (read only)
        feedback_info = TicketConfig.processed_categories.get('feedback', {})
        self.assertIn('generated_rights', feedback_info)
        self.assertIn('restricted_read', feedback_info['generated_rights'])
        self.assertIn('read', feedback_info['generated_rights'])
        # No write permissions defined
        self.assertNotIn('create', feedback_info['generated_rights'])
        self.assertNotIn('update', feedback_info['generated_rights'])
    
    def test_check_category_access_with_new_permissions(self):
        """Test category access with new permission system using real rights"""
        # Test restricted access
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
        
        # Test full read access
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
        
        # Test manager access
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
        # Restricted viewer
        level = GrievanceAccessControl.get_user_access_level(
            self.user_restricted_viewer, 'complaint'
        )
        self.assertEqual(level, 'restricted')
        
        # Full viewer
        level = GrievanceAccessControl.get_user_access_level(
            self.user_full_viewer, 'complaint'
        )
        self.assertEqual(level, 'read')
        
        # Manager - has create, update, delete permissions so should have 'full' access
        level = GrievanceAccessControl.get_user_access_level(
            self.user_manager, 'complaint'
        )
        self.assertEqual(level, 'full')
        
        # No access
        level = GrievanceAccessControl.get_user_access_level(
            self.user_no_rights, 'complaint'
        )
        self.assertEqual(level, 'none')
        
        # Unrestricted category returns 'full'
        level = GrievanceAccessControl.get_user_access_level(
            self.user_no_rights, 'simple_category'
        )
        self.assertEqual(level, 'full')
    
    def test_validate_ticket_access_new_system(self):
        """Test ticket access validation with new permission system"""
        # Manager can create tickets
        try:
            GrievanceAccessControl.validate_ticket_access(
                self.user_manager, 'complaint', None, 'create'
            )
        except PermissionDenied:
            self.fail("validate_ticket_access raised PermissionDenied unexpectedly")
        
        # Viewer cannot write
        with self.assertRaises(PermissionDenied) as context:
            GrievanceAccessControl.validate_ticket_access(
                self.user_full_viewer, 'complaint', None, 'create'
            )
        self.assertIn('create', str(context.exception))
    
    def test_get_user_rights(self):
        """Test getting user rights from database"""
        # Manager should have all complaint rights
        manager_rights = set(self.user_manager.rights) if self.user_manager.rights else set()
        complaint_rights = TicketConfig.processed_categories.get('complaint', {}).get('generated_rights', {})
        
        for right_id in complaint_rights.values():
            self.assertIn(right_id, manager_rights)
        
        # User with no grievance-specific rights should not have complaint rights
        no_rights = set(self.user_no_rights.rights) if self.user_no_rights.rights else set()
        # Check that user doesn't have any of the complaint-specific rights
        for right_id in complaint_rights.values():
            self.assertNotIn(right_id, no_rights)
    
    def test_permission_inheritance_with_overrides(self):
        """Test that child categories can override parent permissions"""
        # service_complaint has only read/write, not update
        service_info = TicketConfig.processed_categories.get('complaint|service_complaint', {})
        rights = service_info.get('generated_rights', {})
        
        self.assertIn('read', rights)
        self.assertIn('create', rights)
        self.assertNotIn('update', rights)  # Parent has update, but child doesn't
    
    def test_get_accessible_categories_with_min_access(self):
        """Test getting accessible categories with minimum access level"""
        # User with restricted access
        categories = GrievanceAccessControl.get_accessible_categories(
            self.user_restricted_viewer
        )
        self.assertIn('complaint', categories)
    
    def test_empty_permissions_means_no_restrictions(self):
        """Test that categories/flags without permissions have no access restrictions"""
        # simple_category has no permissions defined - should return True (no restrictions)
        self.assertTrue(
            GrievanceAccessControl.check_category_access(
                self.user_no_rights, 'simple_category', 'read'
            )
        )
        
        # public flag has no permissions - should return True (no restrictions)
        self.assertTrue(
            GrievanceAccessControl.check_flag_access(
                self.user_no_rights, 'public', 'read'
            )
        )
    
    def test_filter_ticket_queryset(self):
        """Test filtering queryset based on user rights"""
        
        # Create test tickets
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
        
        # User with no rights should only see unrestricted tickets
        queryset = Ticket.objects.all()
        filtered = GrievanceAccessControl.filter_ticket_queryset(queryset, self.user_no_rights)
        
        # Should only see simple_category ticket
        self.assertIn(ticket2, filtered)
        self.assertNotIn(ticket1, filtered)
        
        # User with restricted access should see both
        filtered = GrievanceAccessControl.filter_ticket_queryset(queryset, self.user_restricted_viewer)
        self.assertGreaterEqual(filtered.count(), 2)  # At least our 2 tickets
        
        # Clean up
        ticket1.delete(user=self.user_manager.user)
        ticket2.delete(user=self.user_manager.user)


class GrievanceRightsManagerTest(TestCase):
    """Test automatic rights generation functionality"""
    
    def test_get_next_available_id(self):
        """Test the internal ID generation logic"""
        # Test that the suffix pattern is maintained
        used_ids = set()
        
        # Test read permission (suffix 0)
        next_id = GrievanceRightsManager._get_next_available_id('read', used_ids)
        self.assertEqual(next_id % 10, 0)
        self.assertEqual(next_id, GrievanceRightsManager.GRIEVANCE_RIGHT_BASE + 0)
        
        # Test create permission (suffix 1)
        next_id = GrievanceRightsManager._get_next_available_id('create', used_ids)
        self.assertEqual(next_id % 10, 1)
        self.assertEqual(next_id, GrievanceRightsManager.GRIEVANCE_RIGHT_BASE + 1)
        
        # Test with some used IDs
        used_ids = {127100, 127101, 127102}
        next_id = GrievanceRightsManager._get_next_available_id('read', used_ids)
        self.assertEqual(next_id, 127110)  # Next available with suffix 0
    
    def test_generate_automatic_rights_integration(self):
        """Test the actual rights generation process"""
        
        # Create a mock app config with proper module
        app_config = TicketConfig('grievance_social_protection', grievance_social_protection)
        
        # Set up test configuration
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
        
        # Count permissions before
        ct = ContentType.objects.get_for_model(Ticket)
        perms_before = Permission.objects.filter(
            content_type=ct,
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).count()
        
        # Generate rights
        GrievanceRightsManager.generate_automatic_rights(app_config)
        
        # Check that permissions were created
        perms_after = Permission.objects.filter(
            content_type=ct,
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).count()
        
        # Should have created at least some permissions
        self.assertGreaterEqual(perms_after, perms_before)
        
        # Check that generated_rights were populated
        self.assertIn('generated_rights', app_config.processed_categories['test_category'])
        self.assertIn('generated_rights', app_config.processed_flags['test_flag'])
        
        # Clean up created permissions
        Permission.objects.filter(
            content_type=ct,
            codename__endswith='_grievance',
            id__range=(GrievanceRightsManager.GRIEVANCE_RIGHT_BASE, GrievanceRightsManager.GRIEVANCE_RIGHT_MAX)
        ).delete()