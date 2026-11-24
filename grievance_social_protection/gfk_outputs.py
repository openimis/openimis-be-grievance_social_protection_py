"""
The GenericForeignKey outputs (reporter, commenter) of the grievance lists, loaded
for the whole page at once by core.gfk (OP-3343).
"""
from core.gfk import prefetch_gfk

# Targets whose output reads a relation as well: loaded with it.
TARGET_RELATED = {
    "social_protection.Beneficiary": ("individual",),
}


def prefetch_gfk_outputs(queryset, info, name):
    # The names and birth date are read from the target too.
    reads = (name, f"{name}FirstName", f"{name}LastName", f"{name}Dob")
    return prefetch_gfk(queryset, name, info=info, reads={name: reads}, related=TARGET_RELATED)
