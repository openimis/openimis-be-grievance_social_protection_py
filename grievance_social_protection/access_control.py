import logging
from django.core.exceptions import PermissionDenied

from .apps import TicketConfig

logger = logging.getLogger(__name__)

class GrievanceAccessControl:
    """
    Handles rights-based access control for grievance categories and flags.
    
    Access rules:
    1. Categories/flags can have permissions that generate automatic rights
    2. Users need specific rights to access categories/flags
    3. Restricted view shows limited information based on restricted_read right
    """

    @classmethod
    def check_category_access(cls, user, category_name, access_type='read'):
        """
        Check if user has specific access to a category.
        
        Args:
            user: Django user object
            category_name: Full category name
            access_type: Type of access ('restricted_read', 'read', 'write', 'update')
        
        Returns:
            bool: True if user has the requested access
        """
        if not user or user.is_anonymous:
            return False
        
        processed_categories = getattr(TicketConfig, 'processed_categories', {})
        if not processed_categories or category_name not in processed_categories:
            # No restrictions defined - return None to indicate no restrictions
            return None
        
        category_info = processed_categories[category_name]
        generated_rights = category_info.get('generated_rights', {})
        
        # If no rights generated, no restrictions
        if not generated_rights:
            return None
        
        # Check if user has the specific right
        required_right = generated_rights.get(access_type)
        if not required_right:
            return False
        
        # Use the built-in has_perm method from User model
        return user.has_perm(str(required_right))
    
    @classmethod
    def check_flag_access(cls, user, flag_name, access_type='read'):
        """
        Check if user has specific access to a flag.
        
        Args:
            user: Django user object
            flag_name: Flag name
            access_type: Type of access ('restricted_read', 'read', 'write')
        
        Returns:
            bool: True if user has the requested access
        """
        if not user or user.is_anonymous:
            return False

        processed_flags = getattr(TicketConfig, 'processed_flags', {})
        if not processed_flags or flag_name not in processed_flags:
            # No restrictions defined - return None to indicate no restrictions
            return None
        
        flag_info = processed_flags[flag_name]
        generated_rights = flag_info.get('generated_rights', {})
        
        # If no rights generated, no restrictions
        if not generated_rights:
            return None
        
        # Check if user has the specific right
        required_right = generated_rights.get(access_type)
        if not required_right:
            return False
        
        # Use the built-in has_perm method from User model
        return user.has_perm(str(required_right))
    
    @classmethod
    def get_user_access_level(cls, user, category_name=None, flag_names=None):
        """
        Determine the highest level of access a user has.
        
        Returns:
            str: 'full', 'read', 'restricted', or 'none'
        """
        category_access = None
        flag_access = None
        
        # Check category access
        if category_name:
            # Check for full access (create, update, delete)
            create_access = cls.check_category_access(user, category_name, 'create')
            update_access = cls.check_category_access(user, category_name, 'update')
            delete_access = cls.check_category_access(user, category_name, 'delete')
            read_access = cls.check_category_access(user, category_name, 'read')
            restricted_access = cls.check_category_access(user, category_name, 'restricted_read')
            
            # Skip if category has no restrictions
            if read_access is None and restricted_access is None:
                category_access = None  # No restrictions
            elif create_access or update_access or delete_access:
                # If user has any write permission, they have full access
                category_access = 'full'
            elif read_access:
                category_access = 'read'
            elif restricted_access:
                category_access = 'restricted'
            else:
                category_access = 'none'
        
        # Check flag access - most restrictive across different flags
        if flag_names:
            flag_list = flag_names.split() if isinstance(flag_names, str) else flag_names
            flag_accesses = []
            
            for flag in flag_list:
                # Check each access level - highest permission for each individual flag
                create_access = cls.check_flag_access(user, flag, 'create')
                update_access = cls.check_flag_access(user, flag, 'update')
                delete_access = cls.check_flag_access(user, flag, 'delete')
                read_access = cls.check_flag_access(user, flag, 'read')
                restricted_access = cls.check_flag_access(user, flag, 'restricted_read')
                
                # Skip flags with no restrictions (None means no restrictions)
                if read_access is None and restricted_access is None:
                    continue
                
                # For each flag, determine the actual access level
                if create_access or update_access or delete_access:
                    # If user has any write permission, they have full access
                    flag_accesses.append('full')
                elif read_access:
                    # Having read satisfies restricted_read requirement
                    flag_accesses.append('read')
                elif restricted_access:
                    flag_accesses.append('restricted')
                else:
                    flag_accesses.append('none')
            
            # Across different flags, most restrictive wins
            if flag_accesses:
                if 'none' in flag_accesses:
                    flag_access = 'none'
                elif 'restricted' in flag_accesses:
                    # If any flag only allows restricted access, that's the max
                    flag_access = 'restricted'
                elif 'read' in flag_accesses:
                    flag_access = 'read'
                elif 'full' in flag_accesses:
                    flag_access = 'full'
        
        # Combine category and flag access
        # Category restrictions always take precedence
        if category_access == 'none' or flag_access == 'none':
            return 'none'
        
        # If category has restricted access, that's the maximum allowed
        if category_access == 'restricted':
            return 'restricted'
        
        # If we have both category and flag access
        if category_access is not None and flag_access is not None:
            # Return the most restrictive access
            if category_access == 'restricted' or flag_access == 'restricted':
                return 'restricted'
            elif category_access == 'read' or flag_access == 'read':
                return 'read'
            else:
                return 'full'
        
        # If only one is set, use that
        if category_access is not None:
            return category_access
        if flag_access is not None:
            return flag_access
            
        # No restrictions on anything
        return 'full'
    
    @classmethod
    def get_accessible_categories(cls, user, min_access='restricted_read'):
        """
        Return list of categories accessible to the user.
        
        Args:
            user: The user to check access for
            min_access: Minimum access level required ('restricted_read', 'read', 'write')
        
        Returns:
            List of category names the user can access
        """

        all_categories = list(TicketConfig.grievance_types)
        processed_categories = getattr(TicketConfig, 'processed_categories', {})
        
        if not processed_categories:
            return all_categories
        
        accessible_categories = []
        
        for category_name in all_categories:
            access = cls.check_category_access(user, category_name, min_access)
            if access is True or access is None:  # True = has access, None = no restrictions
                accessible_categories.append(category_name)
        
        return accessible_categories
    
    @classmethod
    def get_accessible_flags(cls, user, min_access='restricted_read'):
        """Return list of flags accessible to the user"""
        
        all_flags = list(TicketConfig.grievance_flags)
        processed_flags = getattr(TicketConfig, 'processed_flags', {})
        
        if not processed_flags:
            return all_flags
        
        accessible_flags = []
        
        for flag_name in all_flags:
            access = cls.check_flag_access(user, flag_name, min_access)
            if access is True or access is None:  # True = has access, None = no restrictions
                accessible_flags.append(flag_name)
        
        return accessible_flags
    
    @classmethod
    def validate_ticket_access(cls, user, category, flags=None, access_type='create'):
        """
        Validate if user can perform action on ticket with given category and flags.
        Raises PermissionDenied if access is not allowed.
        """
        # Check category access
        if category:
            access = cls.check_category_access(user, category, access_type)
            if access is False:  # Explicitly denied
                raise PermissionDenied(f"User does not have {access_type} permission for category: {category}")
        
        # Check flags access
        if flags:
            flag_list = flags.split() if isinstance(flags, str) else flags
            for flag in flag_list:
                access = cls.check_flag_access(user, flag, access_type)
                if flag and access is False:  # Explicitly denied
                    raise PermissionDenied(f"User does not have {access_type} permission for flag: {flag}")
    
    @classmethod
    def filter_ticket_queryset(cls, queryset, user):
        """
        Filter a ticket queryset based on user's access rights.
        
        Args:
            queryset: Django queryset of tickets
            user: User to check permissions for
            
        Returns:
            Filtered queryset
        """
        
        # Get categories user can at least view with restricted access
        accessible_categories = cls.get_accessible_categories(user, 'restricted_read')
        
        # Filter tickets by accessible categories
        if accessible_categories is not None:
            if hasattr(TicketConfig, 'processed_categories') and TicketConfig.processed_categories:
                queryset = queryset.filter(category__in=accessible_categories)
        
        # Further filter by flag permissions
        if hasattr(TicketConfig, 'processed_flags') and TicketConfig.processed_flags:
            # Get flags that user cannot access at all
            restricted_flags = []
            for flag_name, flag_info in TicketConfig.processed_flags.items():
                if flag_info.get('generated_rights'):
                    # Check if user has either read or restricted_read access
                    read_access = cls.check_flag_access(user, flag_name, 'read')
                    restricted_access = cls.check_flag_access(user, flag_name, 'restricted_read')
                    
                    # If user has neither read nor restricted_read, they can't access tickets with this flag
                    if not read_access and not restricted_access:
                        restricted_flags.append(flag_name)
            
            # Exclude tickets with completely restricted flags
            if restricted_flags:
                for flag in restricted_flags:
                    queryset = queryset.exclude(flags__icontains=flag)
        
        return queryset
    
    @classmethod
    def get_category_defaults(cls, category_name):
        """Get default flags and priority for a category"""
        
        processed_categories = getattr(TicketConfig, 'processed_categories', {})
        if not processed_categories or category_name not in processed_categories:
            return {'priority': 'Medium', 'default_flags': []}
        
        category_info = processed_categories[category_name]
        return {
            'priority': category_info.get('priority', 'Medium'),
            'default_flags': category_info.get('default_flags', [])
        }
    
    @classmethod
    def get_effective_priority(cls, category_name, flag_names=None):
        """
        Get the effective priority for a ticket based on category and flags.
        Higher priority wins (Critical > High > Medium > Low).
        """
        
        priorities = ['Low', 'Medium', 'High', 'Critical']
        max_priority = 'Medium'  # Default
        
        # Check category priority
        processed_categories = getattr(TicketConfig, 'processed_categories', {})
        if processed_categories and category_name in processed_categories:
            cat_priority = processed_categories[category_name].get('priority', 'Medium')
            if priorities.index(cat_priority) > priorities.index(max_priority):
                max_priority = cat_priority
        
        # Check flag priorities
        if flag_names:
            processed_flags = getattr(TicketConfig, 'processed_flags', {})
            flag_list = flag_names.split() if isinstance(flag_names, str) else flag_names
            
            for flag_name in flag_list:
                if processed_flags and flag_name in processed_flags:
                    flag_priority = processed_flags[flag_name].get('priority', 'Medium')
                    if priorities.index(flag_priority) > priorities.index(max_priority):
                        max_priority = flag_priority
        
        return max_priority
    
    @classmethod
    def get_visible_fields(cls, user, category_name):
        """
        Get the list of fields visible to the user for a specific category.
        
        Args:
            user: Django user object
            category_name: Full category name
            
        Returns:
            list: List of field names the user can see, or None if all fields are visible
        """
        
        # Check user's access level
        access_level = cls.get_user_access_level(user, category_name)
        
        # Full access or no restrictions - all fields visible
        if access_level == 'full' or access_level == 'read':
            return None  # None means all fields visible
        
        # No access - no fields visible
        if access_level == 'none':
            return []
        
        # Restricted access - check visible_fields configuration
        if access_level == 'restricted':
            processed_categories = getattr(TicketConfig, 'processed_categories', {})
            if processed_categories and category_name in processed_categories:
                category_info = processed_categories[category_name]
                visible_fields = category_info.get('visible_fields', [])
                
                # If visible_fields is defined, return it
                if visible_fields:
                    return visible_fields.copy()
                
                # If no visible_fields at all, restricted users see basic fields only
                return ['id', 'status', 'date_created']
        
        return []
    
    @classmethod
    def filter_fields_for_user(cls, user, category_name, available_fields):
        """
        Filter the available fields based on user's access level.
        
        Args:
            user: Django user object
            category_name: Full category name
            available_fields: Dict of all available fields
            
        Returns:
            dict: Filtered fields the user can access
        """
        visible_fields = cls.get_visible_fields(user, category_name)
        
        # If None, all fields are visible
        if visible_fields is None:
            return available_fields
        
        # Filter to only visible fields
        filtered_fields = {}
        for field_name, field_config in available_fields.items():
            if field_name in visible_fields:
                filtered_fields[field_name] = field_config
        
        return filtered_fields
    
    @classmethod
    def get_category_hierarchy(cls, user):
        """Return hierarchical structure of categories accessible to the user"""
        
        processed_categories = getattr(TicketConfig, 'processed_categories', {})
        if not processed_categories:
            return [{"name": cat, "children": []} for cat in TicketConfig.grievance_types]
        
        hierarchy = []
        
        # Build hierarchy from processed categories
        for category_name, category_info in processed_categories.items():
            if not category_info.get('parent'):
                access = cls.check_category_access(user, category_name, 'restricted_read')
                if access is True or access is None:  # Has access or no restrictions
                    category_dict = {
                    'name': category_name,
                    'priority': category_info.get('priority', 'Medium'),
                    'permissions': category_info.get('permissions', []),
                    'default_flags': category_info.get('default_flags', []),
                    'children': [],
                    'access_level': cls.get_user_access_level(user, category_name)
                }
                
                # Add accessible children
                for child_name, child_info in processed_categories.items():
                    if child_info.get('parent') == category_name:
                        child_access = cls.check_category_access(user, child_name, 'restricted_read')
                        if child_access is True or child_access is None:  # Has access or no restrictions
                            child_dict = {
                            'name': child_name.split('|')[-1],
                            'full_name': child_name,
                            'priority': child_info.get('priority', category_info.get('priority', 'Medium')),
                            'permissions': child_info.get('permissions', []),
                            'default_flags': child_info.get('default_flags', []),
                            'access_level': cls.get_user_access_level(user, child_name)
                            }
                            category_dict['children'].append(child_dict)
                
                hierarchy.append(category_dict)
        
        return hierarchy