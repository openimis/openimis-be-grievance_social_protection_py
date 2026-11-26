import json
import re

from django.core.serializers.json import DjangoJSONEncoder

camel_pat = re.compile(r'([A-Z])')
under_pat = re.compile(r'_([a-z])')


def camel_to_underscore(name):
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
    return under_pat.sub(lambda x: x.group(1).upper(), name)


def model_obj_to_json(model_obj):
    # A copy: the instance may be a prefetched target shared with other rows.
    model_obj_dict = {underscore_to_camel(k): v for k, v in model_obj.__dict__.items() if k != '_state'}
    return json.dumps(model_obj_dict, cls=DjangoJSONEncoder)
