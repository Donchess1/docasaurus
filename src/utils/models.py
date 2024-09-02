import uuid

from django.http import Http404
from django.shortcuts import get_object_or_404


def get_instance_or_404(model_class, id_or_reference):
    # Check if the argument is a UUID
    try:
        uuid_obj = uuid.UUID(str(id_or_reference))
        return get_object_or_404(model_class, id=uuid_obj)
    except ValueError:
        pass

    # Check if the argument is a digit, treat it as an ID
    if isinstance(id_or_reference, int) or (
        isinstance(id_or_reference, str) and id_or_reference.isdigit()
    ):
        return get_object_or_404(model_class, id=id_or_reference)

    # Otherwise, treat it as a reference
    return get_object_or_404(model_class, reference=id_or_reference)
