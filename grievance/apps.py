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

}


class TicketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grievance_social_protection'
    gql_query_tickets_perms = []
    gql_mutation_create_tickets_perms = []
    gql_mutation_update_tickets_perms = []
    gql_mutation_delete_tickets_perms = []
    gql_query_categorys_perms = []
    gql_mutation_create_categorys_perms = []
    gql_mutation_update_categorys_perms = []
    gql_mutation_delete_categorys_perms = []
    tickets_attachments_root_path = None

    def _configure_perms(self, cfg):
        TicketConfig.default_validations_disabled = cfg["default_validations_disabled"]
        TicketConfig.gql_query_tickets_perms = cfg["gql_query_tickets_perms"]
        TicketConfig.gql_mutation_create_tickets_perms = cfg["gql_mutation_create_tickets_perms"]
        TicketConfig.gql_mutation_update_tickets_perms = cfg["gql_mutation_update_tickets_perms"]
        TicketConfig.gql_mutation_delete_tickets_perms = cfg["gql_mutation_delete_tickets_perms"]
        TicketConfig.gql_query_categorys_perms = cfg["gql_query_categorys_perms"]
        TicketConfig.gql_mutation_create_categorys_perms = cfg["gql_mutation_create_categorys_perms"]
        TicketConfig.gql_mutation_update_categorys_perms = cfg["gql_mutation_update_categorys_perms"]
        TicketConfig.gql_mutation_delete_categorys_perms = cfg["gql_mutation_delete_categorys_perms"],
        TicketConfig.tickets_attachments_root_path = cfg["tickets_attachments_root_path"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_perms(cfg)
