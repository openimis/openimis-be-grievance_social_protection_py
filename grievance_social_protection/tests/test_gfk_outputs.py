"""
OP-3343: the reporter of tickets and the commenter of comments (and the names
and birth dates read from them) are loaded for the whole page at once, not with
one query per row, and the JSON they return is unchanged.
"""
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from graphene import Schema
from graphene.test import Client

from core.models.openimis_graphql_test_case import BaseTestContext
from social_protection.models import Beneficiary
from social_protection.tests.test_helpers import create_benefit_plan, create_individual

from grievance_social_protection.models import Comment, Ticket
from grievance_social_protection.schema import Query
from grievance_social_protection.tests.test_helpers import (
    collect_all_rights, create_user_with_rights, restore_grievance_config, setup_grievance_config,
)
from grievance_social_protection.util import underscore_to_camel

PREFIX = "GFK3343"
ROWS = 6
FEW = 3

REPORTER_FIELDS = "reporter reporterType reporterTypeName reporterFirstName reporterLastName reporterDob"
COMMENTER_FIELDS = "commenter commenterType commenterTypeName commenterFirstName commenterLastName commenterDob"


def _legacy_json(obj):
    # What model_obj_to_json returned before OP-3343: the instance's fields, camelCased.
    data = {underscore_to_camel(k): v for k, v in obj.__dict__.items() if k != '_state'}
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def _load(value):
    # The resolvers return a JSON string, which graphene's JSONString encodes again.
    value = json.loads(value)
    return json.loads(value) if isinstance(value, str) else value


def _person(target):
    # The individual whose names and birth date the *FirstName/*LastName/*Dob fields return.
    if isinstance(target, Beneficiary):
        return target.individual
    return target if hasattr(target, 'dob') and hasattr(target, 'first_name') else None


class GenericForeignKeyOutputTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._config = setup_grievance_config({'grievance_types': ['Default'], 'grievance_flags': ['Default']})
        cls.user = create_user_with_rights('gfk3343', [127000, 127004] + list(collect_all_rights()), 'GFK3343Role')
        username = cls.user.username
        individuals = [create_individual(username, {'first_name': f'{PREFIX}{i}'}) for i in range(2)]
        benefit_plan = create_benefit_plan(username, {'code': PREFIX, 'name': PREFIX})
        beneficiary = Beneficiary(individual=individuals[1], benefit_plan=benefit_plan, status='ACTIVE')
        beneficiary.save(username=username)
        # The first FEW rows already hold every reporter type, so a longer page adds rows
        # only. Rows 0 and 3 share an individual, so a prefetched target is reused.
        reporters = [individuals[0], beneficiary, cls.user, individuals[0], beneficiary, individuals[1]]
        for i, reporter in enumerate(reporters):
            ticket = Ticket(title=f"{PREFIX}-{i}", code=f"{PREFIX}-{i}", category='Default', flags='Default',
                            priority='Low', status='OPEN', channel='Web', reporter=reporter)
            ticket.save(user=cls.user)
            comment = Comment(ticket=ticket, comment=f"{PREFIX}-{i}", commenter=reporter)
            comment.save(user=cls.user)

    @classmethod
    def tearDownClass(cls):
        restore_grievance_config(cls._config)
        super().tearDownClass()

    def _execute(self, query):
        result = Client(Schema(query=Query)).execute(query, context=BaseTestContext(self.user).get_request())
        self.assertIsNone(result.get('errors'), result.get('errors'))
        return result['data']

    def _count_queries(self, query):
        self._execute(query)  # warm the caches (rights, content types) first
        with CaptureQueriesContext(connection) as ctx:
            data = self._execute(query)
        return len(ctx), data

    def _assert_constant(self, template):
        few, data = self._count_queries(template % FEW)
        self.assertEqual(len(next(iter(data.values()))['edges']), FEW)
        many, data = self._count_queries(template % ROWS)
        self.assertEqual(len(next(iter(data.values()))['edges']), ROWS)
        self.assertEqual(few, many, f"{few} queries for {FEW} rows, {many} for {ROWS}")

    TICKETS = '{ tickets(first: %%d, code_Istartswith: "%s", orderBy: ["code"]) { edges { node {' \
              ' code %s } } } }' % (PREFIX, REPORTER_FIELDS)
    HISTORY = '{ tickets(first: %%d, showHistory: true, code_Istartswith: "%s", orderBy: ["code"]) {' \
              ' edges { node { code %s } } } }' % (PREFIX, REPORTER_FIELDS)
    COMMENTS = '{ comments(first: %%d, comment_Istartswith: "%s", orderBy: ["comment"]) { edges { node {' \
               ' comment %s } } } }' % (PREFIX, COMMENTER_FIELDS)

    def test_tickets_query_count_does_not_depend_on_rows(self):
        self._assert_constant(self.TICKETS)

    def test_ticket_history_query_count_does_not_depend_on_rows(self):
        self._assert_constant(self.HISTORY)

    def test_comments_query_count_does_not_depend_on_rows(self):
        self._assert_constant(self.COMMENTS)

    def _assert_output(self, node, target, prefix):
        person = _person(target)
        self.assertEqual(_load(node[prefix]), _legacy_json(target))
        self.assertEqual(node[f'{prefix}FirstName'], person.first_name if person else None)
        self.assertEqual(node[f'{prefix}LastName'], person.last_name if person else None)
        self.assertEqual(node[f'{prefix}Dob'], str(person.dob) if person and person.dob else None)

    def test_ticket_output_is_unchanged(self):
        for query in (self.TICKETS, self.HISTORY):
            for edge in self._execute(query % ROWS)['tickets']['edges']:
                node = edge['node']
                ticket = Ticket.objects.get(code=node['code'])
                target = ticket.reporter_type.get_object_for_this_type(pk=ticket.reporter_id)
                with self.subTest(code=node['code'], history='showHistory' in query):
                    self._assert_output(node, target, 'reporter')
                    self.assertEqual(node['reporterTypeName'], ticket.reporter_type.name)

    def test_comment_output_is_unchanged(self):
        for edge in self._execute(self.COMMENTS % ROWS)['comments']['edges']:
            node = edge['node']
            comment = Comment.objects.get(comment=node['comment'])
            target = comment.commenter_type.get_object_for_this_type(pk=comment.commenter_id)
            with self.subTest(comment=node['comment']):
                self._assert_output(node, target, 'commenter')

    def test_rows_sharing_a_reporter_both_return_it(self):
        edges = self._execute(self.TICKETS % ROWS)['tickets']['edges']
        shared = [_load(edges[i]['node']['reporter']) for i in (0, 3)]
        self.assertEqual(shared[0], shared[1])
        self.assertEqual(shared[1]['firstName'], f'{PREFIX}0')
