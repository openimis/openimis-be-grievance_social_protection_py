from django.test import TestCase

from core.test_helpers import create_test_interactive_user
from grievance_social_protection.apps import TicketConfig
from grievance_social_protection.models import Ticket


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
        config = {
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
        
        # Process configuration
        TicketConfig._TicketConfig__process_unified_categories(config)
        TicketConfig._TicketConfig__process_unified_flags(config)
        TicketConfig._TicketConfig__load_config(config)
        
        # Generate rights for the configuration
        cls._generate_test_rights()
    
    @classmethod
    def _generate_test_rights(cls):
        """Use the actual GrievanceRightsManager to generate rights"""
        from grievance_social_protection.rights import GrievanceRightsManager
        
        # Generate rights using the real rights manager
        GrievanceRightsManager.generate_automatic_rights(TicketConfig)
    
    @classmethod
    def _create_test_users(cls):
        """Create test users with different permission levels"""
        # User with all permissions
        cls.user_all_perms = create_test_interactive_user(username='user_all_perms', roles=[7])  # Admin role
        # Add all generated grievance rights to admin user
        all_generated_rights = ['127000']  # Base query permission
        for cat_info in TicketConfig.processed_categories.values():
            if cat_info.get('generated_rights'):
                all_generated_rights.extend(str(right_id) for right_id in cat_info['generated_rights'].values())
        for flag_info in TicketConfig.processed_flags.values():
            if flag_info.get('generated_rights'):
                all_generated_rights.extend(str(right_id) for right_id in flag_info['generated_rights'].values())
        cls._add_permissions_to_user(cls.user_all_perms, all_generated_rights)
        
        # User with limited permissions (only basic query permission)
        cls.user_limited = create_test_interactive_user(username='user_limited', roles=[1])  # Basic role
        # Only add base query permission - no grievance-specific rights
        cls._add_permissions_to_user(cls.user_limited, ['127000'])  # Base query permission only
        
        # User with mixed permissions - can read sensitive flag
        cls.user_mixed = create_test_interactive_user(username='user_mixed', roles=[1])  # Basic role
        # Add base query and sensitive flag read permission
        sensitive_rights = TicketConfig.processed_flags.get('sensitive', {}).get('generated_rights', {})
        perms = ['127000']  # Base query permission
        if sensitive_rights.get('read'):
            perms.append(str(sensitive_rights['read']))
        cls._add_permissions_to_user(cls.user_mixed, perms)
    
    @classmethod
    def _add_permissions_to_user(cls, user, permission_codes):
        """Add specific permissions to a user"""
        if hasattr(user, 'i_user') and user.i_user:
            # Add to the user's rights through their role
            from core.models import Role, RoleRight, UserRole
            
            # Create a custom role for this user
            role = Role.objects.create(
                name=f"TestRole_{user.username}",
                is_system=0,
                is_blocked=False,
                audit_user_id=-1
            )
            
            # Add rights to the role
            for perm_code in permission_codes:
                RoleRight.objects.create(
                    role=role,
                    right_id=int(perm_code),
                    audit_user_id=-1
                )
            
            # Assign role to user
            UserRole.objects.create(
                user=user.i_user,
                role=role,
                audit_user_id=-1
            )
    
    @classmethod
    def _create_test_tickets(cls):
        """Create test tickets"""
        # Create tickets with user for history tracking
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
        # Get all ticket IDs before cleanup
        ticket_ids = [t.id for t in cls.tickets.values()]
        # Delete using a single query
        Ticket.objects.filter(id__in=ticket_ids).delete()
        super().tearDownClass()
    
    def test_filter_all_permissions(self):
        """Test filtering with all permissions"""
        # Admin user should see all tickets
        test_ticket_ids = [t.id for t in self.tickets.values()]
        queryset = Ticket.objects.filter(id__in=test_ticket_ids)
        
        filtered = Ticket.get_queryset(queryset, self.user_all_perms)
        
        # Should see all 4 test tickets
        ticket_ids = list(filtered.values_list('id', flat=True))
        
        # Check each ticket individually
        for name, ticket in self.tickets.items():
            self.assertIn(ticket.id, ticket_ids, 
                         f"Admin user should see '{name}' ticket (category={ticket.category}, flags={ticket.flags})")
    
    def test_filter_limited_permissions(self):
        """Test filtering with limited permissions"""
        # User with only basic permissions
        queryset = Ticket.objects.all()
        filtered = Ticket.get_queryset(queryset, self.user_limited)
        
        ticket_ids = list(filtered.values_list('id', flat=True))
        
        # Should only see public category tickets (no restricted permissions)
        self.assertIn(self.tickets['public'].id, ticket_ids)
        # Should NOT see these due to category/flag restrictions
        self.assertNotIn(self.tickets['restricted'].id, ticket_ids)  # Needs read permission for restricted_category
        self.assertNotIn(self.tickets['sensitive'].id, ticket_ids)   # Needs read permission for sensitive_category
        self.assertNotIn(self.tickets['confidential'].id, ticket_ids)  # Needs read permission for confidential flag
    
    def test_filter_no_config(self):
        """Test filtering when no config exists"""
        # Save and clear config
        original_cats = TicketConfig.processed_categories
        original_flags = TicketConfig.processed_flags
        TicketConfig.processed_categories = {}
        TicketConfig.processed_flags = {}
        
        try:
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.user_limited)
            # Should return all when no config
            self.assertEqual(queryset.count(), filtered.count())
        finally:
            # Restore config
            TicketConfig.processed_categories = original_cats
            TicketConfig.processed_flags = original_flags
    
    def test_filter_mixed_flags(self):
        """Test filtering with mixed flag permissions"""
        # Create ticket with multiple flags
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
            # User has read permission for sensitive flag
            self.assertIn(mixed_ticket.id, ticket_ids)
            # But not for confidential flag
            self.assertNotIn(self.tickets['confidential'].id, ticket_ids)
        finally:
            mixed_ticket.delete(username=self.user_mixed.username)
    
    def test_filter_hierarchical_categories(self):
        """Test filtering with hierarchical categories"""
        # Add parent-child categories
        config = {
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
        
        # Process config
        TicketConfig._TicketConfig__process_unified_categories(config)
        TicketConfig._TicketConfig__process_unified_flags(config)
        TicketConfig._TicketConfig__load_config(config)
        
        # Generate rights for the new configuration
        self._generate_test_rights()
        
        # Create hierarchical tickets
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