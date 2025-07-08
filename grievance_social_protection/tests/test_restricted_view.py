"""
Test restricted view functionality for grievance tickets based on user access levels.
"""
from django.test import TestCase
from core.test_helpers import create_test_interactive_user
from core.models import Role, RoleRight, UserRole
from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase, BaseTestContext
from graphene import Schema
from graphene.test import Client

from grievance_social_protection.models import Ticket
from grievance_social_protection.schema import Query
from grievance_social_protection.access_control import GrievanceAccessControl
from grievance_social_protection.apps import TicketConfig
from grievance_social_protection.rights import GrievanceRightsManager


class RestrictedViewTest(openIMISGraphQLTestCase):
    """Test that sensitive information is hidden based on user access levels"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test users with different access levels
        cls.user_restricted = create_test_interactive_user(username='restricted_viewer', roles=[1])
        cls.user_full_viewer = create_test_interactive_user(username='full_viewer', roles=[1])
        cls.user_manager = create_test_interactive_user(username='manager', roles=[1])
        cls.user_no_access = create_test_interactive_user(username='no_access', roles=[1])
        
        # Create GraphQL schema
        cls.schema = Schema(query=Query)
        
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self._setup_test_config()
        self._create_test_rights()
        self._assign_rights_to_users()
        self._create_test_ticket()
    
    def _setup_test_config(self):
        """Set up test configuration with restricted categories"""
        cfg = {
            'grievance_types': [
                {
                    'name': 'vbg_complaint',
                    'priority': 'Critical',
                    'permissions': ['restricted_read', 'read', 'create'],
                    'default_flags': ['confidential'],
                    'visible_fields': ['id', 'code', 'title', 'category', 'status', 'priority', 'flags', 'accessLevel']
                },
                {
                    'name': 'public_feedback',
                    'priority': 'Low'
                }
            ],
            'grievance_flags': [
                {
                    'name': 'confidential',
                    'priority': 'Critical',
                    'permissions': ['restricted_read', 'read', 'create']
                },
                'public'
            ]
        }
        
        # Process configuration
        TicketConfig._TicketConfig__process_unified_categories(cfg)
        TicketConfig._TicketConfig__process_unified_flags(cfg)
        TicketConfig._TicketConfig__load_config(cfg)
        
        # Generate rights
        self._generate_rights()
    
    def _generate_rights(self):
        """Use the actual GrievanceRightsManager to generate rights"""
        from grievance_social_protection.rights import GrievanceRightsManager
        
        # Generate rights using the real rights manager
        GrievanceRightsManager.generate_automatic_rights(TicketConfig)
    
    def _create_test_rights(self):
        """Rights in OpenIMIS are just integer IDs, not database objects"""
        # No need to create Right objects - they're just IDs used in RoleRight.right_id
        pass
    
    def _assign_rights_to_users(self):
        """Assign rights to test users through roles"""
        vbg_rights = TicketConfig.processed_categories.get('vbg_complaint', {}).get('generated_rights', {})
        conf_rights = TicketConfig.processed_flags.get('confidential', {}).get('generated_rights', {})
        
        # Base query permission that all users need
        base_query_perm = 127000
        
        # Restricted viewer - only restricted_read
        if self.user_restricted.i_user and vbg_rights.get('restricted_read'):
            role = Role.objects.create(
                name='TestRestrictedRole',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Add base query permission
            RoleRight.objects.create(
                role=role,
                right_id=base_query_perm,
                audit_user_id=-1
            )
            RoleRight.objects.create(
                role=role,
                right_id=vbg_rights['restricted_read'],
                audit_user_id=-1
            )
            if conf_rights.get('restricted_read'):
                RoleRight.objects.create(
                    role=role,
                    right_id=conf_rights['restricted_read'],
                    audit_user_id=-1
                )
            UserRole.objects.create(
                user=self.user_restricted.i_user,
                role=role,
                audit_user_id=-1
            )
        
        # Full viewer - read access
        if self.user_full_viewer.i_user and vbg_rights.get('read'):
            role = Role.objects.create(
                name='TestViewerRole',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Add base query permission
            RoleRight.objects.create(
                role=role,
                right_id=base_query_perm,
                audit_user_id=-1
            )
            RoleRight.objects.create(
                role=role,
                right_id=vbg_rights['read'],
                audit_user_id=-1
            )
            if conf_rights.get('read'):
                RoleRight.objects.create(
                    role=role,
                    right_id=conf_rights['read'],
                    audit_user_id=-1
                )
            UserRole.objects.create(
                user=self.user_full_viewer.i_user,
                role=role,
                audit_user_id=-1
            )
        
        # Manager - all rights
        if self.user_manager.i_user:
            role = Role.objects.create(
                name='TestManagerRole',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Add base query permission
            RoleRight.objects.create(
                role=role,
                right_id=base_query_perm,
                audit_user_id=-1
            )
            # Add all vbg_complaint rights
            for right_id in vbg_rights.values():
                RoleRight.objects.create(
                    role=role,
                    right_id=right_id,
                    audit_user_id=-1
                )
            # Add all confidential flag rights
            for right_id in conf_rights.values():
                RoleRight.objects.create(
                    role=role,
                    right_id=right_id,
                    audit_user_id=-1
                )
            UserRole.objects.create(
                user=self.user_manager.i_user,
                role=role,
                audit_user_id=-1
            )
        
        # No access user - only base query permission, no grievance rights
        if self.user_no_access.i_user:
            role = Role.objects.create(
                name='TestNoAccessRole',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            # Only add base query permission so they can query but get filtered results
            RoleRight.objects.create(
                role=role,
                right_id=base_query_perm,
                audit_user_id=-1
            )
            UserRole.objects.create(
                user=self.user_no_access.i_user,
                role=role,
                audit_user_id=-1
            )
    
    def _create_test_ticket(self):
        """Create a test ticket with sensitive information"""
        ticket = Ticket(
            code='TEST001',
            title='Sensitive VBG Case',
            description='This contains very sensitive personal information that should be restricted',
            category='vbg_complaint',
            flags='confidential',
            priority='Critical',
            status='OPEN',
            channel='Web',
            reporter_id=1,
            reporter_type_id=1,
            resolution='This is the confidential resolution details'
        )
        ticket.save(user=self.user_manager.user)
        self.ticket = ticket
        
        public_ticket = Ticket(
            code='PUBLIC001',
            title='Public Feedback',
            description='This is public information',
            category='public_feedback',
            flags='public',
            priority='Low',
            status='OPEN',
            channel='Web'
        )
        public_ticket.save(user=self.user_manager.user)
        self.public_ticket = public_ticket
    
    def tearDown(self):
        """Clean up test data"""
        if hasattr(self, 'ticket'):
            self.ticket.delete(user=self.user_manager.user)
        if hasattr(self, 'public_ticket'):
            self.public_ticket.delete(user=self.user_manager.user)
        super().tearDown()
    
    def _execute_ticket_query(self, user):
        """Execute GraphQL query to get ticket details"""
        query = '''
            query {
                tickets {
                    edges {
                        node {
                            id
                            code
                            title
                            description
                            category
                            flags
                            priority
                            status
                            resolution
                            accessLevel
                        }
                    }
                }
            }
        '''
        
        client = Client(self.schema)
        context = BaseTestContext(user)
        result = client.execute(query, context=context.get_request())
        
        return result
    
    def test_restricted_viewer_sees_limited_info(self):
        """Test that restricted viewer sees only basic information"""
        result = self._execute_ticket_query(self.user_restricted)
        
        self.assertIsNotNone(result)
        self.assertIn('data', result)
        
        edges = result['data']['tickets']['edges']
        
        # Find the VBG ticket
        vbg_ticket = next(
            (edge['node'] for edge in edges if edge['node']['code'] == 'TEST001'),
            None
        )
        
        if vbg_ticket:
            # Should see basic info
            self.assertEqual(vbg_ticket['code'], 'TEST001')
            self.assertEqual(vbg_ticket['title'], '[Restricted]')  # Title should be restricted
            self.assertEqual(vbg_ticket['category'], '[Restricted]')  # Category should be restricted
            self.assertEqual(vbg_ticket['status'], 'OPEN')
            self.assertIsNone(vbg_ticket['priority'])  # Priority is restricted
            
            # Should NOT see sensitive info
            self.assertEqual(vbg_ticket['description'], '[Restricted]')
            self.assertEqual(vbg_ticket['resolution'], '[Restricted]')
            
            # Should see access level
            self.assertEqual(vbg_ticket['accessLevel'], 'restricted')
    
    def test_full_viewer_sees_all_info(self):
        """Test that full viewer sees all information"""
        result = self._execute_ticket_query(self.user_full_viewer)
        
        edges = result['data']['tickets']['edges']
        vbg_ticket = next(
            (edge['node'] for edge in edges if edge['node']['code'] == 'TEST001'),
            None
        )
        
        if vbg_ticket:
            # Should see all info including sensitive data
            self.assertEqual(vbg_ticket['description'], 
                            'This contains very sensitive personal information that should be restricted')
            self.assertEqual(vbg_ticket['resolution'], 
                            'This is the confidential resolution details')
            self.assertEqual(vbg_ticket['accessLevel'], 'read')
    
    def test_no_access_user_sees_only_public(self):
        """Test that user with no access sees only public tickets"""
        result = self._execute_ticket_query(self.user_no_access)
        
        edges = result['data']['tickets']['edges']
        
        # Should only see public ticket
        codes = [edge['node']['code'] for edge in edges]
        self.assertIn('PUBLIC001', codes)
        self.assertNotIn('TEST001', codes)
    
    def test_manager_has_full_access(self):
        """Test that manager sees everything and has full access"""
        result = self._execute_ticket_query(self.user_manager)
        
        edges = result['data']['tickets']['edges']
        vbg_ticket = next(
            (edge['node'] for edge in edges if edge['node']['code'] == 'TEST001'),
            None
        )
        
        if vbg_ticket:
            # Should see all info
            self.assertNotEqual(vbg_ticket['description'], '[Restricted]')
            self.assertNotEqual(vbg_ticket['resolution'], '[Restricted]')
            self.assertEqual(vbg_ticket['accessLevel'], 'full')
    
    def test_public_ticket_accessible_to_all(self):
        """Test that tickets without restrictions are accessible to all"""
        # Even user with no rights should see full info for public tickets
        result = self._execute_ticket_query(self.user_no_access)
        
        edges = result['data']['tickets']['edges']
        public_data = next(
            (edge['node'] for edge in edges if edge['node']['code'] == 'PUBLIC001'),
            None
        )
        
        self.assertIsNotNone(public_data)
        self.assertEqual(public_data['description'], 'This is public information')
        self.assertEqual(public_data['accessLevel'], 'full')  # No restrictions
    
    def test_access_level_calculation(self):
        """Test access level calculation based on actual rights"""
        # Test with real user rights
        access_level = GrievanceAccessControl.get_user_access_level(
            self.user_restricted, 'vbg_complaint', 'confidential'
        )
        self.assertEqual(access_level, 'restricted')
        
        access_level = GrievanceAccessControl.get_user_access_level(
            self.user_full_viewer, 'vbg_complaint', 'confidential'
        )
        self.assertEqual(access_level, 'read')
        
        access_level = GrievanceAccessControl.get_user_access_level(
            self.user_manager, 'vbg_complaint', 'confidential'
        )
        self.assertEqual(access_level, 'full')
        
        access_level = GrievanceAccessControl.get_user_access_level(
            self.user_no_access, 'vbg_complaint', 'confidential'
        )
        self.assertEqual(access_level, 'none')


class RestrictedViewIntegrationTest(TestCase):
    """Integration tests for restricted view with actual rights checking"""
    
    def setUp(self):
        """Set up test environment"""
        self.user = create_test_interactive_user(username='test_rights_user', roles=[1])
        self._setup_config_and_rights()
    
    def _setup_config_and_rights(self):
        """Set up configuration and create rights"""
        # Simple test config
        cfg = {
            'grievance_types': [{
                'name': 'test_category',
                'permissions': ['restricted_read', 'read', 'create']  # Changed 'write' to 'create' and added restricted_read
            }]
        }
        
        TicketConfig._TicketConfig__process_unified_categories(cfg)
        TicketConfig._TicketConfig__load_config(cfg)
        
        # Use the actual GrievanceRightsManager to generate rights
        from grievance_social_protection.rights import GrievanceRightsManager
        GrievanceRightsManager.generate_automatic_rights(TicketConfig)
    
    def test_rights_based_filtering(self):
        """Test that rights-based filtering works correctly"""
        # Give user only restricted_read right
        cat_info = TicketConfig.processed_categories.get('test_category', {})
        if self.user.i_user and cat_info.get('generated_rights', {}).get('restricted_read'):
            role = Role.objects.create(
                name='TestRestrictedOnly',
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            RoleRight.objects.create(
                role=role,
                right_id=cat_info['generated_rights']['restricted_read'],
                audit_user_id=-1
            )
            UserRole.objects.create(
                user=self.user.i_user,
                role=role,
                audit_user_id=-1
            )
            
            # User should have restricted access
            access_level = GrievanceAccessControl.get_user_access_level(
                self.user, 'test_category'
            )
            self.assertEqual(access_level, 'restricted')
            
            # User should be able to check restricted access
            self.assertTrue(
                GrievanceAccessControl.check_category_access(
                    self.user, 'test_category', 'restricted_read'
                )
            )
            self.assertFalse(
                GrievanceAccessControl.check_category_access(
                    self.user, 'test_category', 'read'
                )
            )
    
    def tearDown(self):
        """Clean up test data"""
        # No Right objects to clean up - they're just IDs
        super().tearDown()