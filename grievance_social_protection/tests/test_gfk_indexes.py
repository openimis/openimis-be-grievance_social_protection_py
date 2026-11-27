"""
OP-3342: the GenericForeignKey pairs of tickets and comments have a composite
(type, id) index, so that looking rows up by reporter or commenter does not scan
the table.
"""
from django.db import connection
from django.test import TestCase

from grievance_social_protection.models import Comment, Ticket

GFK_PAIRS = [
    (Ticket, "reporter_type", "reporter_id"),
    (Comment, "commenter_type", "commenter_id"),
]


class GenericForeignKeyIndexTest(TestCase):
    def test_every_gfk_pair_has_a_type_id_index(self):
        for model, type_field, id_field in GFK_PAIRS:
            table = model._meta.db_table
            columns = [model._meta.get_field(f).column for f in (type_field, id_field)]
            with self.subTest(table=table, columns=columns):
                with connection.cursor() as cursor:
                    constraints = connection.introspection.get_constraints(cursor, table)
                self.assertTrue(
                    any(c["index"] and c["columns"][:2] == columns for c in constraints.values()),
                    f"no ({', '.join(columns)}) index on {table}",
                )
