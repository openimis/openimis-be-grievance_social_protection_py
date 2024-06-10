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
                'id', 'key', 'title', 'code',
                'description', 'attending_staff',
                'status', 'category', 'flags',
                'channel', 'resolution'
            ]
            queryset_pagination = 5000
