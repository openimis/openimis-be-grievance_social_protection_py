from django.apps import AppConfig

MODULE_NAME = "grievance"

DEFAULT_CFG = {
    "gql_query_grievances_perms": ["115001"],
    "gql_query_grievance_perms": ["115001"],
    "gql_mutation_create_grievance_perms": ["115002"],
    "gql_mutation_update_grievance_perms": ["115003"],
    "gql_mutation_delete_grievance_perms": ["115004"],
}

class GrievanceConfig(AppConfig):
    name = 'grievance'

    gql_query_grievance_perms = []
    gql_query_grievance_perms = []
    gql_mutation_create_grievance_perms = []
    gql_mutation_update_grievance_perms = []
    gql_mutation_delete_grievance_perms = []



    def _configure_permissions(self, cfg):
        GrievanceConfig.gql_query_grievance_perms = cfg["gql_query_grievance_perms"]
        GrievanceConfig.gql_query_grievance_perms = cfg["gql_query_grievance_perms"]
        GrievanceConfig.gql_mutation_create_grievance_perms = cfg["gql_mutation_create_grievance_perms"]
        GrievanceConfig.gql_mutation_update_grievance_perms = cfg["gql_mutation_update_grievance_perms"]
        GrievanceConfig.gql_mutation_delete_grievance_perms = cfg["gql_mutation_delete_grievance_perms"]


    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
