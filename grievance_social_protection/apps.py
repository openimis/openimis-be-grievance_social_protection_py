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
    "default_responses": {DEFAULT_STRING: DEFAULT_STRING},
    "grievance_anonymized_fields": {DEFAULT_STRING: []}
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
    grievance_anonymized_fields = {}

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__validate_grievance_dict_fields(cfg, 'default_responses')
        self.__validate_grievance_dict_fields(cfg, 'grievance_anonymized_fields')
        self.__load_config(cfg)

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
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(TicketConfig, field):
                setattr(TicketConfig, field, cfg[field])
