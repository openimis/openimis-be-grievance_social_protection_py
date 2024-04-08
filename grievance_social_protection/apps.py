from django.apps import AppConfig

MODULE_NAME = "grievance_social_protection"

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

    "grievance_types": ["Default"],
    "grievance_flags": ["Default"],
    "grievance_channels": ["Default"],
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

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)

    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(TicketConfig, field):
                setattr(TicketConfig, field, cfg[field])
