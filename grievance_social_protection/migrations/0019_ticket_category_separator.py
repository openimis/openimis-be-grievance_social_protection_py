import logging

from django.db import migrations

logger = logging.getLogger(__name__)

LEGACY_SEPARATOR = '|'
CATEGORY_SEPARATOR = ' > '


def rewrite_pipe_categories(apps, schema_editor):
    """
    Sub-categories were stored 'parent|child' until the separator became ' > '
    (grievance_social_protection.apps.CATEGORY_SEPARATOR). Every category lookup
    compares the stored name with the configured one, so such a ticket was left out
    of every ticket list and its category's rights and defaults did not apply.

    Rewrites those names once. A name that is itself a configured category is a flat
    category whose name contains a pipe, and is kept. Only the current rows are
    rewritten: the ticket history keeps the name as it was stored at the time.
    """
    from grievance_social_protection.apps import TicketConfig

    Ticket = apps.get_model('grievance_social_protection', 'Ticket')
    configured = set(TicketConfig.processed_categories or ())
    legacy_names = (
        Ticket.objects
        .filter(category__contains=LEGACY_SEPARATOR)
        .exclude(category__in=configured)
        .values_list('category', flat=True)
        .distinct()
    )
    for legacy_name in list(legacy_names):
        current_name = CATEGORY_SEPARATOR.join(part.strip() for part in legacy_name.split(LEGACY_SEPARATOR))
        count = Ticket.objects.filter(category=legacy_name).update(category=current_name)
        logger.info("Ticket category '%s' rewritten to '%s' on %s ticket(s)", legacy_name, current_name, count)


class Migration(migrations.Migration):

    dependencies = [
        ('grievance_social_protection', '0018_alter_comment_user_created_and_more'),
    ]

    operations = [
        # No reverse: a ' > ' name rewritten here cannot be told apart from one
        # written with ' > ', and every version that reads tickets expects ' > '.
        migrations.RunPython(rewrite_pipe_categories, migrations.RunPython.noop),
    ]
