from django.db import models
from django.db.models import ForeignObject, F
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, ReverseOneToOneDescriptor
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.query_utils import PathInfo, Q


class CustomForeignObjectRel(ForeignObjectRel):
    """
    Define some extra Field methods so this Rel acts more like a Field, which
    lets us use ReverseManyToOneDescriptor in both directions.
    """
    @property
    def foreign_related_fields(self):
        return []

    def get_attname(self):
        return self.name

    def get_extra_restriction(self, where_class, alias, related_alias):
        return Restriction(False, self.related_model, self.model, related_alias, alias, self.field.join_conditions, where_class)

    def get_forward_related_filter(self, obj):
        """
        Return the filter arguments which select the instances of self.model
        that are related to obj.
        """
        q = self.field.join_conditions

        # If this is a simple restriction that can be expressed as an AND of
        # two basic field lookups, we can return a dictionary of filters...
        if q.connector == Q.AND and all(type(c) != tuple for c in q.children):
            return {
                lookup: getattr(obj, v.name) if isinstance(v, L) else v
                for lookup, v in q.children
            }

        # ...otherwise, we return this lookup and let the compiler figure it
        # out. This will involve a join where the above method might not.
        else:
            return {self.name: obj}


class Restriction(object):
    def __init__(self, forward, local_model, related_model, local_alias, related_alias, join_conditions, where_class):
        self.forward = forward
        self.local_model = local_model
        self.related_model = related_model
        self.related_alias = related_alias
        self.local_alias = local_alias
        self.join_conditions = join_conditions
        self.where_class = where_class

    def as_sql(self, compiler, connection):
        aliases = list(compiler.query.alias_map)
        tables = list(compiler.query.tables)

        assert aliases == tables
        assert {self.local_alias, self.related_alias} <= set(aliases)

        is_forward = aliases.index(self.local_alias) > aliases.index(self.related_alias)
        if not self.forward:
            is_forward = not is_forward
        field_query = compiler.query.clone(**{
            "model": self.local_model,
            "tables": (
                [self.related_alias] + [t for t in compiler.query.tables if t != self.related_alias]
            ) if is_forward else (
                [self.local_alias] + [t for t in compiler.query.tables if t != self.local_alias]
            ),
        })
        lookup_query = compiler.query.clone(**{
            "model": self.related_model,
            "tables": (
                [self.local_alias] + [t for t in compiler.query.tables if t != self.local_alias]
            ) if is_forward else (
                [self.related_alias] + [t for t in compiler.query.tables if t != self.related_alias]
            ),
        })
        lookup_query._relationship_field_query = field_query
        q = self.join_conditions.resolve_expression(lookup_query, False, compiler.query.used_aliases)
        result = compiler.compile(q)
        return result


class Relationship(models.ForeignObject):
    """
    This is a Django model field.
    """

    auto_created = False

    many_to_many = False
    many_to_one = True
    one_to_many = False
    one_to_one = False

    rel_class = CustomForeignObjectRel

    def __init__(self, to, join_conditions, **kwargs):
        if kwargs.pop('multiple', True):
            self.accessor_class = ReverseManyToOneDescriptor
        else:
            self.accessor_class = ReverseOneToOneDescriptor
        if kwargs.pop('reverse_multiple', True):
            self.related_accessor_class = ReverseManyToOneDescriptor
        else:
            self.related_accessor_class = ReverseOneToOneDescriptor

        super(Relationship, self).__init__(to, models.DO_NOTHING, [], [], **kwargs)
        self.join_conditions = join_conditions

    @property
    def field(self):
        """
        Makes ReverseManyToOneDescriptor work in both directions.
        """
        return self.remote_field

    def get_accessor_name(self):
        return self.name

    def get_extra_restriction(self, where_class, related_alias, local_alias):

        # opts = [self.rel.to._meta, self.model._meta]
        # aliases = [related_alias, local_alias]

        # def build_condition(expression, *args):
        #     local_seq = [isinstance(arg, L) for arg in args]
        #     alias_seq = [aliases[is_local] for is_local in local_seq]
        #     field_seq = [opts[is_local].get_field(arg) for arg, is_local in zip(args, local_seq)]
        #
        #     arg_cols = [field.get_col(alias_or_instance)
        #                 if isinstance(alias_or_instance, six.text_type)
        #                 else field.value_from_object(alias_or_instance)
        #                 for alias_or_instance, field in zip(alias_seq, field_seq)]
        #
        #     return expression(*arg_cols)

        return Restriction(True, self.model, self.related_model, local_alias, related_alias, self.join_conditions, where_class)

    def get_forward_related_filter(self, obj):
        """
        Return the filter arguments which select the instances of self.model
        that are related to obj.
        """
        q = self.field.join_conditions

        # If this is a simple restriction that can be expressed as an AND of
        # two basic field lookups, we can return a dictionary of filters...
        if q.connector == Q.AND and all(type(c) != tuple for c in q.children):
            return {
                lookup: getattr(obj, v.name) if isinstance(v, L) else v
                for lookup, v in q.children
            }

        # ...otherwise, we return this lookup and let the compiler figure it
        # out. This will involve a join where the above method might not.
        else:
            return {self.name: obj}

    def resolve_related_fields(self):
        return []

    def contribute_to_class(self, cls, name, **kwargs):
        kwargs['virtual_only'] = True
        super(ForeignObject, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.accessor_class(self))

    def get_path_info(self):
        to_opts = self.rel.to._meta
        from_opts = self.model._meta
        return [PathInfo(from_opts, to_opts, (to_opts.pk,), self, True, False)]


class L(F):
    def resolve_expression(self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False):
        return super(L, self).resolve_expression(query._relationship_field_query, allow_joins, reuse, summarize, for_save)
