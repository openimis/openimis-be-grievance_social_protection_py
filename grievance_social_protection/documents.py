from django.apps import apps

# Check if the 'opensearch_reports' app is in INSTALLED_APPS
if 'opensearch_reports' in apps.app_configs:
    from django_opensearch_dsl import Document, fields as opensearch_fields
    from django_opensearch_dsl.registries import registry
    from grievance_social_protection.models import Ticket

    @registry.register_document
    class TicketDocument(Document):
        key = opensearch_fields.KeywordField(),
        title = opensearch_fields.KeywordField(),

        description = opensearch_fields.KeywordField(),
        code = opensearch_fields.KeywordField(),
        attending_staff = opensearch_fields.KeywordField(),
        status = opensearch_fields.KeywordField(),

        category = opensearch_fields.KeywordField(),
        flags = opensearch_fields.KeywordField(),
        channel = opensearch_fields.KeywordField(),
        resolution = opensearch_fields.KeywordField(),

        class Index:
            name = 'ticket'
            settings = {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
            auto_refresh = True

        class Django:
            model = Ticket
            fields = [
                'id', 'key', 'title', 'code'
            ]
            queryset_pagination = 5000

        def prepare_json_ext(self, instance):
            json_ext_data = instance.json_ext
            json_data = self.__flatten_dict(json_ext_data)
            return json_data

        def __flatten_dict(self, d, parent_key='', sep='__'):
            items = {}
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.update(self.__flatten_dict(v, new_key, sep=sep))
                else:
                    items[new_key] = v
            return items
