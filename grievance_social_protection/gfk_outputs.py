"""
Loading the GenericForeignKey outputs (reporter, commenter) of a whole page at
once, instead of one query per row (OP-3343).
"""
from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.prefetch import GenericPrefetch
from django.db.models import prefetch_related_objects
from graphql.language import FragmentSpreadNode

from grievance_social_protection.util import underscore_to_camel

# Targets whose output reads a relation as well: loaded with it, per content type.
_TARGET_RELATIONS = {
    ("social_protection", "Beneficiary"): ("individual",),
}


def _requested_fields(info):
    names = set()

    def walk(selection_set):
        for selection in selection_set.selections if selection_set else ():
            if isinstance(selection, FragmentSpreadNode):
                walk(info.fragments[selection.name.value].selection_set)
                continue
            if getattr(selection, "name", None):
                names.add(selection.name.value)
            walk(selection.selection_set)

    for field_node in info.field_nodes:
        walk(field_node.selection_set)
    return names


def _target_querysets():
    querysets = []
    for (app_label, model_name), relations in _TARGET_RELATIONS.items():
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            continue
        # _base_manager, as the GenericForeignKey itself uses: no row is hidden.
        querysets.append(model._base_manager.select_related(*relations))
    return querysets


def prefetch_gfk_outputs(queryset, info, *gfk_names):
    """Prefetch the requested GenericForeignKeys of the page and select their types."""
    requested = _requested_fields(info)
    for name in gfk_names:
        camel = underscore_to_camel(name)
        # The names and birth date are read from the target too.
        reads_target = {camel, f"{camel}FirstName", f"{camel}LastName", f"{camel}Dob"}
        if requested & reads_target:
            lookup = GenericPrefetch(name, _target_querysets())
            if isinstance(getattr(queryset.model, name, None), GenericForeignKey):
                queryset = queryset.prefetch_related(lookup)
            else:
                # the type too: building the ticket drops what select_related loaded
                queryset = _prefetch_after_fetch(queryset, f"{name}_type", lookup)
        if requested & (reads_target | {f"{camel}Type", f"{camel}TypeName"}):
            queryset = queryset.select_related(f"{name}_type")
    return queryset


_after_fetch_classes = {}


def _prefetch_after_fetch(queryset, *new_lookups):
    """
    History rows (`Ticket.history...as_instances()`) have the GenericForeignKey's
    columns but not the field: they only become tickets once fetched, so the
    targets are loaded then, for the page.
    """
    base = type(queryset)
    cls = _after_fetch_classes.get(base)
    if cls is None:
        class PrefetchAfterFetch(base):
            def _clone(self):
                clone = super()._clone()
                clone._gfk_lookups = self._gfk_lookups
                return clone

            def _fetch_all(self):
                fetched = self._result_cache is not None
                super()._fetch_all()
                if not fetched and self._result_cache:
                    instances = [obj for obj in self._result_cache if not isinstance(obj, self.model)]
                    if instances:
                        prefetch_related_objects(instances, *self._gfk_lookups)

        cls = _after_fetch_classes[base] = PrefetchAfterFetch
    queryset = queryset._clone()
    lookups = getattr(queryset, '_gfk_lookups', ())
    queryset.__class__ = cls
    queryset._gfk_lookups = (*lookups, *new_lookups)
    return queryset
