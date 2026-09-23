"""
Guard rails on grievance_social_protection's rights declaration.

Same structure as `claim`, `product` and `contribution_plan`: `DJANGO_PERMS` by entity
then by action, `_PERM_CFG` deriving the config keys from it, and a `get_rights` on
each main model which is only an access point.

What is particular to this module is that it has **two sources of rights**:

  * the STATIC rights, 127000-127006, written in `DJANGO_PERMS` - that is what these
    tests pin down;
  * the DYNAMIC rights, 127100-127999, created at runtime by
    `rights.GrievanceRightsManager` out of `grievance_types`, laid down as
    `*_category_tickets_perms` / `*_flagged_tickets_perms` attributes on the AppConfig
    and read by `GrievanceAccessControl`. They are deliberately not declared: their
    integer depends on the configuration and on the order of the categories.

The tests below lock down the entity/action pair of the static block and, above all,
the **boundary** between the two: no declared identifier may fall in the range reserved
for the generator.
"""

import json
import os

from django.test import TestCase

from grievance_social_protection.apps import (
    DJANGO_PERMS,
    TicketConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)
from grievance_social_protection.models import Comment, Ticket
from grievance_social_protection.rights import GrievanceRightsManager

# The identifiers as deployed. Changing one is incompatible with the existing roles:
# this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "gql_query_tickets_perms": ["127000"],
    "gql_mutation_create_tickets_perms": ["127001"],
    "gql_mutation_update_tickets_perms": ["127002"],
    "gql_mutation_delete_tickets_perms": ["127003"],
    "gql_mutation_resolve_grievance_perms": ["127006"],
    "gql_query_comments_perms": ["127004"],
    "gql_mutation_create_comment_perms": ["127005"],
}

# The `permissions_map.json` entries that carry these identifiers. The historical name
# in the openIMIS catalogue is not the django name declared in DJANGO_PERMS: what has to
# stay stable is the integer.
EXPECTED_MAP_ENTRIES = {
    "grievance_social_protection.tickets": "127000",
    "grievance_social_protection.create_tickets": "127001",
    "grievance_social_protection.update_tickets": "127002",
    "grievance_social_protection.delete_tickets": "127003",
    "grievance_social_protection.comments": "127004",
    "grievance_social_protection.create_comment": "127005",
    "grievance_social_protection.resolve_grievance": "127006",
}

# The two dynamic rights hard-laid on the AppConfig in advance, for the default
# `uncategorized` category. They are outside `DJANGO_PERMS` by design; pinned here so
# that their disappearance or their move is visible.
PRESEEDED_DYNAMIC_RIGHTS = {
    "gql_query_uncategorized_category_tickets_perms": [127100],
    "gql_mutation_update_uncategorized_category_tickets_perms": [127102],
}

MODEL_BY_ENTITY = {
    "ticket": Ticket,
    "comment": Comment,
}


def _permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class GrievancePermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(TicketConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        """`__load_config` ignores the keys with no class attribute."""
        missing = [key for key in _PERM_CFG if not hasattr(TicketConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(TicketConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(TicketConfig, key), perms(entity, action))

    def test_no_right_id_is_shared(self):
        """Seven actions, seven identifiers: no alias in this module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append(f"{entity}.{action}")
        shared = {right: who for right, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("ticket", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("comment", "nosuchaction")

    def test_ids_match_permissions_map(self):
        mapping = _permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json absent de cet assemblage")
        actual = {name: mapping.get(name) for name in EXPECTED_MAP_ENTRIES}
        self.assertEqual(actual, EXPECTED_MAP_ENTRIES)

    # --- the boundary with the generated rights ---------------------------
    def test_no_declared_right_falls_in_the_generated_range(self):
        """
        127100-127999 belongs to `GrievanceRightsManager`. Declaring a fixed integer
        in it would make that integer collide with a permission allocated at runtime,
        and `core/rights_sync.py` would write a false mapping.
        """
        intruders = [
            (entity, action, right_id)
            for entity, actions in DJANGO_PERMS.items()
            for action, (_, right_id) in actions.items()
            if GrievanceRightsManager.GRIEVANCE_RIGHT_BASE
            <= right_id
            <= GrievanceRightsManager.GRIEVANCE_RIGHT_MAX
        ]
        self.assertEqual(intruders, [])

    def test_preseeded_dynamic_rights_stay_out_of_the_declaration(self):
        """
        127100 / 127102 are the identifiers the default `uncategorized` category gets
        **when it is the first** to ask for 'read' and 'update': `_get_next_available_id`
        starts from 127100 + suffix and advances by 10 in the iteration order of
        `processed_categories`. Two deployments with the same categories in a different
        order therefore do not assign the same integers. These two values stay a
        pre-seeding on the AppConfig, never a declaration.
        """
        for key in PRESEEDED_DYNAMIC_RIGHTS:
            with self.subTest(key=key):
                self.assertNotIn(key, _PERM_CFG)
                self.assertTrue(hasattr(TicketConfig, key))

    # --- the access point through the model -------------------------------
    def test_each_model_exposes_every_action_of_its_entity(self):
        for entity, model in MODEL_BY_ENTITY.items():
            for action in DJANGO_PERMS[entity]:
                with self.subTest(entity=entity, action=action):
                    self.assertEqual(
                        model.get_rights(action), configured_perms(entity, action)
                    )
                    self.assertTrue(model.get_rights(action))

    def test_model_returns_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        for model in MODEL_BY_ENTITY.values():
            with self.subTest(model=model.__name__):
                self.assertIsNone(model.get_rights("nosuchaction"))

    def test_model_reads_the_configured_value_not_the_declared_default(self):
        original = TicketConfig.gql_query_tickets_perms
        try:
            TicketConfig.gql_query_tickets_perms = ["999999"]
            self.assertEqual(Ticket.get_rights("query"), ["999999"])
            self.assertEqual(perms("ticket", "query"), ["127000"])
        finally:
            TicketConfig.gql_query_tickets_perms = original

    # --- the sub-resource --------------------------------------------------
    def test_comment_delegates_update_and_delete_to_its_ticket(self):
        """
        The comment has its own read and create rights, but no modify right:
        `model_rights` then walks up to the ticket through `scope_parent`. `ticket` is
        the only owning FK - `commenter` denotes the author.
        """
        from core.rights_scope import model_rights, scope_parent_of

        self.assertEqual(Comment.scope_parent, "ticket")
        self.assertIs(scope_parent_of(Comment), Ticket)
        for action in ("update", "delete"):
            with self.subTest(action=action):
                self.assertIsNone(Comment.get_rights(action))
                self.assertEqual(
                    model_rights(Comment, action), configured_perms("ticket", action)
                )
