"""
Rights Manager for grievance categories and flags.
"""
import logging
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Ticket

logger = logging.getLogger(__name__)


class GrievanceRightsManager:
    """Manages automatic rights generation for grievance categories and flags"""

    # Reserve 127100-127999 for dynamic grievance permissions
    GRIEVANCE_RIGHT_BASE = 127100
    GRIEVANCE_RIGHT_MAX = 127999

    @classmethod
    def generate_automatic_rights(cls, app_config):
        """
        Generate automatic rights using Django's auth_permission table.
        Permissions are stored persistently to maintain stable IDs across config changes.
        """
        
        # Get content type for Ticket model
        try:
            ct = ContentType.objects.get_for_model(Ticket)
        except Exception as e:
            logger.warning(f"Could not get ContentType for Ticket model: {e}")
            return
        
        # Get all existing grievance permissions from the reserved range
        existing_perms = Permission.objects.filter(
            content_type=ct,
            codename__endswith='_grievance',
            id__range=(cls.GRIEVANCE_RIGHT_BASE, cls.GRIEVANCE_RIGHT_MAX)
        )
        
        # Build map of existing permissions by codename
        existing_by_codename = {perm.codename: perm for perm in existing_perms}
        
        # Get used IDs in our range
        used_ids = set(Permission.objects.filter(
            id__range=(cls.GRIEVANCE_RIGHT_BASE, cls.GRIEVANCE_RIGHT_MAX)
        ).values_list('id', flat=True))
        
        all_rights = {}  # Collect all rights
        
        # Process categories
        processed_categories = getattr(app_config, 'processed_categories', {})
        
        for category_name, category_info in processed_categories.items():
            permissions = category_info.get('permissions', [])
            if permissions:
                # Convert back to list format if still dict
                if isinstance(permissions, dict):
                    permissions = list(permissions.keys())
                
                category_info['generated_rights'] = {}
                safe_name = category_name.lower().replace(' ', '_').replace('|', '_')
                
                for perm_type in permissions:
                    # Generate codename
                    codename = f"{perm_type}_{safe_name}_grievance"
                    
                    # Check if permission already exists
                    if codename in existing_by_codename:
                        perm = existing_by_codename[codename]
                        category_info['generated_rights'][perm_type] = perm.id
                        logger.info(f"Using existing permission: {codename} (ID: {perm.id})")
                    else:
                        # Generate new ID following suffix pattern
                        try:
                            new_id = cls._get_next_available_id(perm_type, used_ids)
                            
                            # Create new permission
                            perm = Permission.objects.create(
                                id=new_id,
                                codename=codename,
                                name=f"Can {perm_type.replace('_', ' ')} {category_name} tickets",
                                content_type=ct
                            )
                            
                            category_info['generated_rights'][perm_type] = perm.id
                            used_ids.add(new_id)
                            logger.info(f"Created new permission: {codename} (ID: {new_id})")
                        except ValueError as e:
                            logger.error(f"Failed to create permission {codename}: {e}")
                            continue
                    
                    # Add to all_rights with OpenIMIS naming convention
                    if perm_type == 'restricted_read':
                        right_name = f"gql_query_restricted_{safe_name}_category_tickets_perms"
                    elif perm_type == 'read':
                        right_name = f"gql_query_{safe_name}_category_tickets_perms"
                    elif perm_type == 'create':
                        right_name = f"gql_mutation_create_{safe_name}_category_tickets_perms"
                    elif perm_type == 'update':
                        right_name = f"gql_mutation_update_{safe_name}_category_tickets_perms"
                    elif perm_type == 'delete':
                        right_name = f"gql_mutation_delete_{safe_name}_category_tickets_perms"
                    else:
                        continue
                    
                    all_rights[right_name] = category_info['generated_rights'][perm_type]
        
        # Process flags
        processed_flags = getattr(app_config, 'processed_flags', {})
        
        for flag_name, flag_info in processed_flags.items():
            permissions = flag_info.get('permissions', [])
            if permissions:
                # Convert back to list format if still dict
                if isinstance(permissions, dict):
                    permissions = list(permissions.keys())
                
                flag_info['generated_rights'] = {}
                safe_name = flag_name.lower().replace(' ', '_')
                
                for perm_type in permissions:
                    # Generate codename
                    codename = f"{perm_type}_flag_{safe_name}_grievance"
                    
                    # Check if permission already exists
                    if codename in existing_by_codename:
                        perm = existing_by_codename[codename]
                        flag_info['generated_rights'][perm_type] = perm.id
                        logger.info(f"Using existing permission: {codename} (ID: {perm.id})")
                    else:
                        # Generate new ID following suffix pattern
                        try:
                            new_id = cls._get_next_available_id(perm_type, used_ids)
                            
                            # Create new permission
                            perm = Permission.objects.create(
                                id=new_id,
                                codename=codename,
                                name=f"Can {perm_type.replace('_', ' ')} {flag_name} flagged tickets",
                                content_type=ct
                            )
                            
                            flag_info['generated_rights'][perm_type] = perm.id
                            used_ids.add(new_id)
                            logger.info(f"Created new permission: {codename} (ID: {new_id})")
                        except ValueError as e:
                            logger.error(f"Failed to create permission {codename}: {e}")
                            continue
                    
                    # Add to all_rights with OpenIMIS naming convention
                    if perm_type == 'restricted_read':
                        right_name = f"gql_query_restricted_{safe_name}_flagged_tickets_perms"
                    elif perm_type == 'read':
                        right_name = f"gql_query_{safe_name}_flagged_tickets_perms"
                    elif perm_type == 'create':
                        right_name = f"gql_mutation_create_{safe_name}_flagged_tickets_perms"
                    elif perm_type == 'update':
                        right_name = f"gql_mutation_update_{safe_name}_flagged_tickets_perms"
                    elif perm_type == 'delete':
                        right_name = f"gql_mutation_delete_{safe_name}_flagged_tickets_perms"
                    else:
                        continue
                    
                    all_rights[right_name] = flag_info['generated_rights'][perm_type]
        
        # Store generated rights for documentation
        app_config.generated_rights = all_rights
        
        # Log summary of permissions
        if all_rights:
            logger.info(f"Generated/verified {len(all_rights)} grievance permissions")
            
            # Group rights by permission name to match OpenIMIS convention
            grouped_rights = {}
            for right_name, right_id in all_rights.items():
                if right_name not in grouped_rights:
                    grouped_rights[right_name] = []
                grouped_rights[right_name].append(right_id)
            
            # Update DEFAULT_CFG with generated permissions
            from .apps import DEFAULT_CFG
            for right_name, right_ids in grouped_rights.items():
                DEFAULT_CFG[right_name] = right_ids
                # Also set as class attribute
                setattr(app_config, right_name, right_ids)

    @classmethod
    def _get_next_available_id(cls, perm_type, used_ids):
        suffix_map = {
            'read': 0,              # -> gql_query_*
            'create': 1,            # -> gql_mutation_create_*
            'update': 2,            # -> gql_mutation_update_*
            'delete': 3,            # -> gql_mutation_delete_*
            'restricted_read': 4,   # -> gql_query_restricted_*
        }
        
        suffix = suffix_map.get(perm_type, 9)
        
        # Start from base and find next available with correct suffix
        candidate = cls.GRIEVANCE_RIGHT_BASE + suffix
        while candidate in used_ids and candidate <= cls.GRIEVANCE_RIGHT_MAX:
            candidate += 10  # Maintain suffix while incrementing
            
        if candidate > cls.GRIEVANCE_RIGHT_MAX:
            raise ValueError(f"No available ID for permission type {perm_type}")
            
        return candidate  