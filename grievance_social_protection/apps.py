import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)

MODULE_NAME = "grievance_social_protection"

DEFAULT_STRING = 'Default'

DEFAULT_CFG = {
    "default_validations_disabled": False,
    "gql_query_tickets_perms": ["123000"],
    "gql_mutation_create_tickets_perms": ["123001"],
    "gql_mutation_update_tickets_perms": ["123002"],
    "gql_mutation_delete_tickets_perms": ["123003"],
    "gql_query_categorys_perms": ["123004"],
    "gql_mutation_create_categorys_perms": ["123005"],
    "gql_mutation_update_categorys_perms": ["123006"],
    "gql_mutation_delete_categorys_perms": ["123007"],
    "tickets_attachments_root_path": None,

    "grievance_types": [DEFAULT_STRING],
    "grievance_flags": [DEFAULT_STRING],
    "grievance_channels": [DEFAULT_STRING],
    "default_responses": {'eloo': DEFAULT_STRING}
}


class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME
    gql_query_tickets_perms = []
    gql_mutation_create_tickets_perms = []
    gql_mutation_update_tickets_perms = []
    gql_mutation_delete_tickets_perms = []
    gql_query_categorys_perms = []
    gql_mutation_create_categorys_perms = []
    gql_mutation_update_categorys_perms = []
    gql_mutation_delete_categorys_perms = []
    tickets_attachments_root_path = None

    grievance_types = []
    grievance_flags = []
    grievance_channels = []
    default_responses = {}

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__validate_grievance_responses(cfg)
        self.__load_config(cfg)

    @classmethod
    def __validate_grievance_responses(cls, cfg):
        def get_grievance_type_options_msg(types):
            types_string = ", ".join(types)
            return logger.info(f'Available grievance types: %s', types_string)

        default_responses = cfg.get('default_responses', {})
        if not default_responses:
            return

        grievance_types = cfg.get('grievance_types', [])
        if not grievance_types:
            logger.warning('Please specify grievance_types if you want to setup default responses.')

        if not isinstance(default_responses, dict):
            get_grievance_type_options_msg(grievance_types)
            return

        for grievance_type_key in default_responses.keys():
            if grievance_type_key not in grievance_types:
                logger.warning(f'%s not in grievance_types', grievance_type_key)
                get_grievance_type_options_msg(grievance_types)

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(TicketConfig, field):
                setattr(TicketConfig, field, cfg[field])
