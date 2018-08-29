from django.db.models import Q

from relativity.fields import L, Relationship


class MPTTRef(L):

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        model = query._relationship_field_query.model
        name = getattr(model._mptt_meta, self.name + "_attr")
        return L(name).resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )


class MPTTQ(Q):

    def __init__(self, *args, **kwargs):
        super(MPTTQ, self).__init__(*args, **kwargs)
        self.filters = kwargs

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        translate_lookups = query.model._tree_manager._translate_lookups
        translated_filters = translate_lookups(**self.filters)
        clone_q = Q(**translated_filters)
        # We must promote any new joins to left outer joins so that when Q is
        # used as an expression, rows aren't filtered due to joins.
        return clone_q.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )


class MPTTDescendants(Relationship):

    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "ascendants")
        kwargs.setdefault("to", "self")
        kwargs.setdefault(
            "predicate",
            MPTTQ(
                tree_id=MPTTRef("tree_id"),
                left__gt=MPTTRef("left"),
                left__lt=MPTTRef("right"),
            ),
        )
        super(MPTTDescendants, self).__init__(**kwargs)


class MPTTSubtree(Relationship):
    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "rootpath")
        kwargs.setdefault("to", "self")
        kwargs.setdefault(
            "predicate",
            MPTTQ(
                tree_id=MPTTRef("tree_id"),
                left__gte=MPTTRef("left"),
                left__lt=MPTTRef("right"),
            ),
        )
        super(MPTTSubtree, self).__init__(**kwargs)
