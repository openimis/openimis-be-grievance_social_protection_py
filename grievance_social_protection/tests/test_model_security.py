"""
Test that security filtering is properly implemented at the model level.
This ensures security is enforced consistently across all endpoints (GraphQL, FHIR, etc.)
"""
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from core.test_helpers import create_test_interactive_user
from grievance_social_protection.models import Ticket, Comment
from grievance_social_protection.apps import TicketConfig


class ModelSecurityTest(TestCase):
    """Test security filtering at the model level"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_test_config()
        cls._create_test_users()
        cls._create_test_tickets()
    
    @classmethod
    def _setup_test_config(cls):
        """Set up test configuration"""
        config = {
            'grievance_types': [
                'public_category',
                {
                    'name': 'restricted_category',
                    'permissions': ['restricted_read', 'read', 'create'],
                    'visible_fields': ['id', 'status', 'priority', 'date_created']
                },
                {
                    'name': 'highly_restricted',
                    'visible_fields': ['id', 'status'],  # Very limited visibility
                    'permissions': ['restricted_read', 'read']
                }
            ],
            'grievance_flags': [
                'public',
                {
                    'name': 'confidential',
                    'permissions': ['read', 'create']
                }
            ]
        }
        
        # Process configuration
        TicketConfig._TicketConfig__process_unified_categories(config)
        TicketConfig._TicketConfig__process_unified_flags(config)
        TicketConfig._TicketConfig__load_config(config)
        
        # Create permissions in test database
        try:
            ct = ContentType.objects.get_for_model(Ticket)
            # Create test permissions with specific IDs
            Permission.objects.get_or_create(
                id=127200,
                defaults={
                    'codename': 'grievance_restricted_category_restricted_read',
                    'name': 'Can restricted read restricted_category tickets',
                    'content_type': ct
                }
            )
            Permission.objects.get_or_create(
                id=127201,
                defaults={
                    'codename': 'grievance_restricted_category_read',
                    'name': 'Can read restricted_category tickets',
                    'content_type': ct
                }
            )
            Permission.objects.get_or_create(
                id=127202,
                defaults={
                    'codename': 'grievance_restricted_category_create',
                    'name': 'Can create restricted_category tickets',
                    'content_type': ct
                }
            )
            Permission.objects.get_or_create(
                id=127421,
                defaults={
                    'codename': 'grievance_flag_confidential_read',
                    'name': 'Can read confidential flagged tickets',
                    'content_type': ct
                }
            )
            Permission.objects.get_or_create(
                id=127422,
                defaults={
                    'codename': 'grievance_flag_confidential_create',
                    'name': 'Can create confidential flagged tickets',
                    'content_type': ct
                }
            )
            
            # Update the processed config with generated rights
            TicketConfig.processed_categories['restricted_category']['generated_rights'] = {
                'restricted_read': 127200,
                'read': 127201,
                'create': 127202
            }
            TicketConfig.processed_flags['confidential']['generated_rights'] = {
                'read': 127421,
                'create': 127422
            }
        except Exception as e:
            cls.stdout.write(f"Warning: Could not create test permissions: {e}")
    
    @classmethod
    def _create_test_users(cls):
        """Create test users with different permission levels"""
        from core.models import Role, RoleRight, UserRole
        from core.utils import TimeUtils
        
        # Admin with all permissions - use admin role
        cls.admin_user = create_test_interactive_user(username='test_admin', roles=[7])  # IMIS Administrator
        
        # Create custom role with all grievance permissions
        admin_role = Role.objects.create(
            name="Test Grievance Admin",
            is_blocked=False,
            is_system=False,
            audit_user_id=-1,
        )
        
        # Add base permissions
        base_perms = [127000, 127001, 127002, 127003, 127004, 127005, 127006]
        # Add test-specific permissions
        test_perms = [127200, 127201, 127202, 127421, 127422]
        
        for perm_id in base_perms + test_perms:
            try:
                RoleRight.objects.create(
                    role=admin_role,
                    right_id=perm_id,
                    audit_user_id=-1,
                    validity_from=TimeUtils.now(),
                )
            except Exception:
                pass
        
        # Assign the custom role to admin user
        UserRole.objects.create(
            user=cls.admin_user.i_user,
            role=admin_role,
            audit_user_id=-1
        )
        
        # Limited user with minimal permissions
        limited_role = Role.objects.create(
            name="Test Limited User",
            is_blocked=False,
            is_system=False,
            audit_user_id=-1,
        )
        
        # Only add base query permission
        RoleRight.objects.create(
            role=limited_role,
            right_id=127000,
            audit_user_id=-1,
            validity_from=TimeUtils.now(),
        )
        
        cls.limited_user = create_test_interactive_user(username='test_limited', roles=[limited_role.id])
    
    @classmethod
    def _create_test_tickets(cls):
        """Create test tickets"""
        cls.tickets = {}
        
        # Public ticket - should be visible to all
        ticket = Ticket(
            title='Public ticket',
            category='public_category',
            flags='public',
            description='This is a public ticket'
        )
        ticket.save(user=cls.admin_user)
        cls.tickets['public'] = ticket
        
        # Create comment on public ticket
        comment = Comment(
            ticket=ticket,
            comment='Public comment',
            is_resolution=False
        )
        comment.save(user=cls.admin_user)
        cls.public_comment = comment
        
        # Restricted category ticket - should only be visible to admin
        ticket = Ticket(
            title='Restricted ticket',
            category='restricted_category',
            flags='public',
            description='This is a restricted ticket'
        )
        ticket.save(user=cls.admin_user)
        cls.tickets['restricted'] = ticket
        
        # Create comment on restricted ticket
        comment = Comment(
            ticket=ticket,
            comment='Restricted comment',
            is_resolution=False
        )
        comment.save(user=cls.admin_user)
        cls.restricted_comment = comment
        
        # Public category with confidential flag - should only be visible to admin
        ticket = Ticket(
            title='Confidential ticket',
            category='public_category',
            flags='confidential',
            description='This is a confidential ticket'
        )
        ticket.save(user=cls.admin_user)
        cls.tickets['confidential'] = ticket
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        # Delete tickets and comments
        Comment.objects.filter(ticket__in=cls.tickets.values()).delete()
        Ticket.objects.filter(id__in=[t.id for t in cls.tickets.values()]).delete()
        super().tearDownClass()
    
    def test_ticket_security_with_row_security_enabled(self):
        """Test ticket filtering with ROW_SECURITY enabled"""
        # Save original setting
        original_setting = getattr(settings, 'ROW_SECURITY', True)
        settings.ROW_SECURITY = True
        
        try:
            # Test admin user
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.admin_user)
            
            # Admin should see all tickets
            self.assertEqual(filtered.count(), 3)
            for name, ticket in self.tickets.items():
                self.assertTrue(
                    filtered.filter(id=ticket.id).exists(),
                    f"Admin should see {name} ticket"
                )
            
            # Test limited user
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, self.limited_user)
            
            # Limited user should only see public ticket
            self.assertEqual(filtered.count(), 1)
            self.assertTrue(
                filtered.filter(id=self.tickets['public'].id).exists(),
                "Limited user should see public ticket"
            )
            self.assertFalse(
                filtered.filter(id=self.tickets['restricted'].id).exists(),
                "Limited user should not see restricted ticket"
            )
            self.assertFalse(
                filtered.filter(id=self.tickets['confidential'].id).exists(),
                "Limited user should not see confidential ticket"
            )
        finally:
            # Restore original setting
            settings.ROW_SECURITY = original_setting
    
    def test_ticket_security_with_row_security_disabled(self):
        """Test ticket filtering with ROW_SECURITY disabled"""
        # Save original setting
        original_setting = getattr(settings, 'ROW_SECURITY', True)
        settings.ROW_SECURITY = False
        
        try:
            # With ROW_SECURITY disabled, all users should see all tickets
            # Filter to only our test tickets to avoid interference from other tests
            our_ticket_ids = [t.id for t in self.tickets.values()]
            queryset = Ticket.objects.filter(id__in=our_ticket_ids)
            filtered = Ticket.get_queryset(queryset, self.limited_user)
            
            # Should see all tickets when security is disabled
            self.assertEqual(filtered.count(), 3)
        finally:
            # Restore original setting
            settings.ROW_SECURITY = original_setting
    
    def test_comment_security_inherits_from_ticket(self):
        """Test that comment security inherits from parent ticket"""
        # Save original setting
        original_setting = getattr(settings, 'ROW_SECURITY', True)
        settings.ROW_SECURITY = True
        
        try:
            # Test admin user
            queryset = Comment.objects.all()
            filtered = Comment.get_queryset(queryset, self.admin_user)
            
            # Admin should see all comments
            self.assertTrue(
                filtered.filter(id=self.public_comment.id).exists(),
                "Admin should see public comment"
            )
            self.assertTrue(
                filtered.filter(id=self.restricted_comment.id).exists(),
                "Admin should see restricted comment"
            )
            
            # Test limited user
            queryset = Comment.objects.all()
            filtered = Comment.get_queryset(queryset, self.limited_user)
            
            # Limited user should only see comment on public ticket
            self.assertTrue(
                filtered.filter(id=self.public_comment.id).exists(),
                "Limited user should see public comment"
            )
            self.assertFalse(
                filtered.filter(id=self.restricted_comment.id).exists(),
                "Limited user should not see restricted comment"
            )
        finally:
            # Restore original setting
            settings.ROW_SECURITY = original_setting
    
    def test_graphql_info_object_handling(self):
        """Test that GraphQL ResolveInfo objects are handled correctly"""
        from graphql import ResolveInfo
        from unittest.mock import Mock
        
        # Create a mock ResolveInfo with user
        mock_info = Mock(spec=ResolveInfo)
        mock_info.context = Mock()
        mock_info.context.user = self.limited_user
        
        # Save original setting
        original_setting = getattr(settings, 'ROW_SECURITY', True)
        settings.ROW_SECURITY = True
        
        try:
            # Test that ResolveInfo is properly handled
            queryset = Ticket.objects.all()
            filtered = Ticket.get_queryset(queryset, mock_info)
            
            # Should extract user from ResolveInfo and apply filtering
            self.assertEqual(filtered.count(), 1)
            self.assertTrue(
                filtered.filter(id=self.tickets['public'].id).exists(),
                "Should handle ResolveInfo object correctly"
            )
        finally:
            settings.ROW_SECURITY = original_setting