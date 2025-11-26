import logging
import sys
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)

MODULE_NAME = "grievance_social_protection"

DEFAULT_STRING = 'Default'
# CRON timedelta: {days},{hours}
DEFAULT_TIME_RESOLUTION = '5,0'
DEFAULT_GRIEVANCE_TYPE = 'uncategorized'

DEFAULT_CFG = {
    "default_validations_disabled": False,
    "default_grievance_type": DEFAULT_GRIEVANCE_TYPE,
    "gql_query_tickets_perms": ["127000"],
    "gql_query_comments_perms": ["127004"],
    "gql_mutation_create_tickets_perms": ["127001"],
    "gql_mutation_update_tickets_perms": ["127002"],
    "gql_mutation_delete_tickets_perms": ["127003"],
    "gql_mutation_create_comment_perms": ["127005"],
    "gql_mutation_resolve_grievance_perms": ["127006"],
    "tickets_attachments_root_path": None,

    "grievance_types": [DEFAULT_STRING, 'Category A', 'Category B'],
    "grievance_flags": [DEFAULT_STRING, 'Flag A', 'Flag B'],
    "grievance_channels": [DEFAULT_STRING, 'Channel A', 'Channel B'],
    "default_responses": {DEFAULT_STRING: DEFAULT_STRING},
    "grievance_anonymized_fields": {DEFAULT_STRING: []},
    # CRON timedelta: {days},{hours}
    "resolution_times": DEFAULT_TIME_RESOLUTION,
    "default_resolution": {DEFAULT_STRING: DEFAULT_TIME_RESOLUTION, 'Category A': '4,0', 'Category B': '6,12'},

    "attending_staff_role_ids": [],
    "default_attending_staff_role_ids": {DEFAULT_STRING: [1, 2]},
}


class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME
    gql_query_tickets_perms = []
    gql_query_comments_perms = []
    gql_mutation_create_tickets_perms = []
    gql_mutation_update_tickets_perms = []
    gql_mutation_delete_tickets_perms = []
    gql_mutation_resolve_grievance_perms = []
    gql_mutation_create_comment_perms = []
    tickets_attachments_root_path = None

    grievance_types = []
    grievance_flags = []
    grievance_channels = []
    default_responses = {}
    grievance_anonymized_fields = {}
    resolution_times = {}
    default_resolution = {}
    default_grievance_type = DEFAULT_GRIEVANCE_TYPE
    attending_staff_role_ids = []
    default_attending_staff_role_ids = {}
    
    # Processed structures for enhanced configurations
    processed_categories = {}
    processed_flags = {}
    unified_resolution_times = {}
    generated_rights = {}  # Store dynamically generated rights
    
    @classmethod
    def get_all_permissions(cls):
        """
        Get all permissions including dynamically generated ones.
        This method can be used by external systems to get the complete permission list.
        """
        all_perms = {}
        
        # Start with static permissions from DEFAULT_CFG
        for key, value in DEFAULT_CFG.items():
            if key.endswith('_perms'):
                all_perms[key] = value
        
        # Add dynamically generated permissions
        for right_name, right_id in cls.generated_rights.items():
            if right_name not in all_perms:
                all_perms[right_name] = []
            if right_id not in all_perms[right_name]:
                all_perms[right_name].append(right_id)
        
        return all_perms

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__process_unified_categories(cfg)
        self.__process_unified_flags(cfg)
        self.__validate_grievance_dict_fields(cfg, 'default_responses')
        self.__validate_grievance_dict_fields(cfg, 'grievance_anonymized_fields')
        self.__validate_grievance_dict_fields(cfg, 'default_resolution')
        self.__validate_grievance_default_resolution_time(cfg)
        self.__load_config(cfg)
        # Generate rights only if we're not in a migration, and NO_DATABASE is set
        if os.environ.get("NO_DATABASE") != "True" and 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            from .rights import GrievanceRightsManager
            GrievanceRightsManager.generate_automatic_rights(self)

    @classmethod
    def __validate_grievance_dict_fields(cls, cfg, field_name):
        def get_grievance_type_options_msg(types):
            types_string = ", ".join(types)
            return logger.info(f'Available grievance types: {types_string}')

        dict_field = cfg.get(field_name, {})
        if not dict_field:
            return

        grievance_types = cfg.get('grievance_types', [])
        if not grievance_types:
            logger.warning('Please specify grievance_types if you want to setup %s.', field_name)

        if not isinstance(dict_field, dict):
            get_grievance_type_options_msg(grievance_types)
            return

        for field_key in dict_field.keys():
            if field_key not in grievance_types:
                logger.warning('%s in %s not in grievance_types', field_key, field_name)
                get_grievance_type_options_msg(grievance_types)

    @classmethod
    def __validate_grievance_default_resolution_time(cls, cfg):
        """
        Validate resolution times from both legacy default_resolution and new category-specific resolution_times.
        This method also builds a unified resolution times mapping that considers:
        1. Category-specific resolution_times (from processed_categories)
        2. Legacy default_resolution configuration
        3. Global resolution_times fallback
        """
        # First, validate legacy default_resolution
        dict_field = cfg.get("default_resolution", {})
        if dict_field:
            for key in dict_field:
                value = dict_field[key]
                if value in ['', None]:
                    resolution_times = cfg.get("resolution_times", DEFAULT_TIME_RESOLUTION)
                    logger.warning(
                        '"%s" has no value for resolution. The default one is taken as "%s".',
                        key,
                        resolution_times
                    )
                    dict_field[key] = resolution_times
                else:
                    cls.__validate_resolution_time_format(value, f"default_resolution[{key}]")
        
        # Then, validate resolution_times in processed categories
        processed_categories = cfg.get("processed_categories", {})
        for category_name, category_info in processed_categories.items():
            resolution_time = category_info.get('resolution_times')
            if resolution_time:
                cls.__validate_resolution_time_format(resolution_time, f"category '{category_name}'")
        
        # Build unified resolution times mapping for backward compatibility
        unified_resolution = {}
        
        # Start with legacy default_resolution
        if dict_field:
            unified_resolution.update(dict_field)
        
        # Override/add with category-specific resolution_times
        for category_name, category_info in processed_categories.items():
            resolution_time = category_info.get('resolution_times')
            if resolution_time:
                unified_resolution[category_name] = resolution_time
        
        # Store the unified mapping back
        cfg['unified_resolution_times'] = unified_resolution
    
    @classmethod
    def __validate_resolution_time_format(cls, value, context=""):
        """Validate a single resolution time format"""
        if ',' not in value:
            logger.warning(f"Invalid resolution time format for {context}. "
                         "Configuration should contain two integers representing days and hours, "
                         "separated by a comma.")
            return False
        
        try:
            parts = value.split(',')
            days = int(parts[0])
            hours = int(parts[1])
            
            if 0 <= days < 99 and 0 <= hours < 24:
                return True
            else:
                logger.warning(f"Invalid resolution time values for {context}. "
                             "Days must be between 0 and 99, and hours must be between 0 and 24.")
                return False
        except (ValueError, IndexError):
            logger.warning(f"Invalid resolution time format for {context}. "
                         "Expected format: 'days,hours' where both are integers.")
            return False

    @classmethod
    def __process_unified_categories(cls, cfg):
        """
        Process grievance_types configuration supporting both string and dict formats
        """
        categories = cfg.get('grievance_types', [])
        processed_categories = {}
        flat_types = []
        
        # Ensure default_grievance_type is in the categories list
        default_grievance_type = cfg.get('default_grievance_type', DEFAULT_GRIEVANCE_TYPE)
        if default_grievance_type:
            # Check if default_grievance_type exists in categories
            type_exists = False
            for cat in categories:
                if isinstance(cat, str) and cat == default_grievance_type:
                    type_exists = True
                    break
                elif isinstance(cat, dict) and cat.get('name') == default_grievance_type:
                    type_exists = True
                    break
            
            # If not found, add it with default permissions
            if not type_exists:
                categories.insert(0, {
                    'name': default_grievance_type,
                    'permissions': ['read', 'update']
                })
                logger.info(f"Added default grievance type '{default_grievance_type}' with permissions ['read', 'update']")
        
        def process_category_item(item, parent_name=None, parent_info=None):
            """Process a single category item (string or dict)"""
            if isinstance(item, str):
                # Simple string format (backward compatible)
                full_name = f"{parent_name}|{item}" if parent_name else item
                processed_categories[full_name] = {
                    'priority': parent_info.get('priority', 'Medium') if parent_info else 'Medium',
                    'permissions': parent_info.get('permissions', []) if parent_info else [],  # Inherit from parent
                    'default_flags': parent_info.get('default_flags', []) if parent_info else [],
                    'resolution_times': parent_info.get('resolution_times') if parent_info else None,
                    'parent': parent_name,
                    'children': {},
                    'generated_rights': {}
                }
                flat_types.append(full_name)
                return full_name
                
            elif isinstance(item, dict):
                # Enhanced dict format with permissions
                cat_name = item.get('name')
                if not cat_name:
                    logger.warning("Category dict must have 'name' field")
                    return None
                
                full_name = f"{parent_name}|{cat_name}" if parent_name else cat_name
                
                # Process permissions - handle both dict and list formats
                permissions = item.get('permissions', parent_info.get('permissions', []) if parent_info else [])
                # Convert dict format to list format if needed
                if isinstance(permissions, dict):
                    permissions = list(permissions.keys())
                
                # Process visible_fields with inheritance constraints
                visible_fields = item.get('visible_fields', [])
                if visible_fields:
                    # If visible_fields is defined, ensure restricted_read and read permissions exist
                    if 'restricted_read' not in permissions:
                        permissions.append('restricted_read')
                        logger.info(f"Auto-adding 'restricted_read' permission to category '{cat_name}' due to visible_fields")
                    if 'read' not in permissions:
                        permissions.append('read')
                        logger.info(f"Auto-adding 'read' permission to category '{cat_name}' due to visible_fields")
                    
                    # Validate against parent's visible_fields
                    if parent_info and parent_info.get('visible_fields'):
                        parent_visible = set(parent_info['visible_fields'])
                        child_visible = set(visible_fields)
                        
                        # Check if child tries to expose fields hidden by parent
                        invalid_fields = child_visible - parent_visible
                        if invalid_fields:
                            logger.warning(
                                f"Category '{cat_name}' cannot make fields {invalid_fields} visible - "
                                f"not in parent's visible_fields. Removing these fields."
                            )
                            # Use intersection to ensure child is subset of parent
                            visible_fields = list(child_visible & parent_visible)
                            item['visible_fields'] = visible_fields
                elif parent_info and parent_info.get('visible_fields'):
                    # Inherit parent's visible_fields if not specified
                    visible_fields = parent_info['visible_fields'].copy()
                
                # Inherit from parent if not specified
                priority = item.get('priority', parent_info.get('priority', 'Medium') if parent_info else 'Medium')
                default_flags = item.get('default_flags', parent_info.get('default_flags', []) if parent_info else [])
                
                # Handle resolution_times - inherit from parent if not specified
                resolution_times = item.get('resolution_times')
                if not resolution_times and parent_info:
                    resolution_times = parent_info.get('resolution_times')
                
                category_info = {
                    'priority': priority,
                    'permissions': permissions,
                    'default_flags': default_flags,
                    'resolution_times': resolution_times,
                    'parent': parent_name,
                    'children': {},
                    'generated_rights': {}  # Will be populated by rights generation
                }
                
                processed_categories[full_name] = category_info
                flat_types.append(full_name)
                
                # Process children recursively
                children = item.get('children', [])
                for child in children:
                    child_full_name = process_category_item(child, full_name, category_info)
                    if child_full_name:
                        child_short_name = child_full_name.split('|')[-1]
                        category_info['children'][child_short_name] = child_full_name
                
                return full_name
            
            return None
        
        # Process all top-level categories
        for category in categories:
            process_category_item(category)
        
        # Store processed data
        cfg['processed_categories'] = processed_categories
        # Update flat list for backward compatibility
        cfg['grievance_types'] = flat_types
        TicketConfig.processed_categories = processed_categories

    @classmethod
    def __process_unified_flags(cls, cfg):
        """
        Process grievance_flags configuration supporting both string and dict formats
        """
        flags = cfg.get('grievance_flags', [])
        processed_flags = {}
        flat_flags = []
        
        for flag in flags:
            if isinstance(flag, str):
                # Simple string format (backward compatible)
                processed_flags[flag] = {
                    'priority': 'Medium',
                    'permissions': [],  # No restrictions - empty list
                    'generated_rights': {}
                }
                flat_flags.append(flag)
                
            elif isinstance(flag, dict):
                # Enhanced dict format with permissions
                flag_name = flag.get('name')
                if not flag_name:
                    logger.warning("Flag dict must have 'name' field")
                    continue
                
                # Process permissions - handle both dict and list formats
                permissions = flag.get('permissions', [])
                # Convert dict format to list format if needed
                if isinstance(permissions, dict):
                    permissions = list(permissions.keys())
                
                processed_flags[flag_name] = {
                    'priority': flag.get('priority', 'Medium'),
                    'permissions': permissions,
                    'generated_rights': {}
                }
                flat_flags.append(flag_name)
        
        # Store processed data
        cfg['processed_flags'] = processed_flags
        # Update flat list for backward compatibility
        cfg['grievance_flags'] = flat_flags
        TicketConfig.processed_flags = processed_flags

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(TicketConfig, field):
                setattr(TicketConfig, field, cfg[field])
    
