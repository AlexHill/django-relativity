from __future__ import absolute_import, division, print_function, unicode_literals

import django.db.migrations.operations.fields


def is_referenced_by_foreign_key(state, model_name_lower, field, field_name):
    """
    This is a hack to work around migration problems when using a Relationship
    field, which has f.to_fields == []. The change is simply to swap the
    operands of an and, so should have no effect on behaviour.

    The monkeypatched code is identical in all supported versions of Django.
    """
    for state_app_label, state_model in state.models:
        for _, f in state.models[state_app_label, state_model].fields:
            if (
                f.related_model
                and "%s.%s" % (state_app_label, model_name_lower)
                == f.related_model.lower()
                and hasattr(f, "to_fields")
            ):
                # Code change is here - the clauses of the and in the parens are switched
                # if (f.to_fields[0] is None and field.primary_key) or field_name in f.to_fields:
                if (
                    field.primary_key and f.to_fields[0] is None
                ) or field_name in f.to_fields:
                    return True
    return False


django.db.migrations.operations.fields.is_referenced_by_foreign_key = (
    is_referenced_by_foreign_key
)
