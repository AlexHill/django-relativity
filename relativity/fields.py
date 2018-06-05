from collections import OrderedDict

import django
from django.db import models, connections
from django.db.models import ForeignObject, F
from django.db.models.fields.related_descriptors import (
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.query_utils import PathInfo, Q
from django.utils.functional import cached_property


class Restriction(object):

    def __init__(
        self,
        forward,
        local_model,
        related_model,
        local_alias,
        related_alias,
        predicate,
        where_class,
    ):
        self.forward = forward
        self.local_model = local_model
        self.related_model = related_model
        self.related_alias = related_alias
        self.local_alias = local_alias
        self.predicate = predicate
        self.where_class = where_class

    def as_sql(self, compiler, connection):
        local, related = self.local_alias, self.related_alias
        alias_map = compiler.query.alias_map

        assert {local, related} <= set(alias_map)

        aliases_local = OrderedDict({local: alias_map[local]})
        aliases_local.update(alias_map)
        aliases_related = OrderedDict({related: alias_map[related]})
        aliases_related.update(alias_map)

        alias_list = list(alias_map)
        if (alias_list.index(local) < alias_list.index(related)) ^ self.forward:
            aliases_local, aliases_related = aliases_related, aliases_local

        field_query = compiler.query.clone()
        field_query.model = self.local_model
        field_query.alias_map = aliases_local

        lookup_query = compiler.query.clone()
        lookup_query.model = self.related_model
        lookup_query.alias_map = aliases_related

        if django.VERSION < (2, 0):
            field_query.tables = list(aliases_local)
            lookup_query.tables = list(aliases_related)

        lookup_query._relationship_field_query = field_query
        q = self.predicate.resolve_expression(
            query=lookup_query, allow_joins=False, reuse=compiler.query.used_aliases
        )
        result = compiler.compile(q)
        return result


def create_relationship_many_manager(base_manager, rel):

    class RelationshipManager(base_manager):

        def __init__(self, instance):
            super(RelationshipManager, self).__init__()

            self.instance = instance
            self.model = rel.related_model
            self.field = rel.field

            self.core_filters = {self.field.name: instance}

        def __call__(self, **kwargs):
            manager = getattr(self.model, kwargs.pop("manager"))
            manager_class = create_relationship_many_manager(manager.__class__, rel)
            return manager_class(self.instance)
        do_not_call_in_templates = True

        def _apply_rel_filters(self, queryset):
            """
            Filter the queryset for the instance this manager is bound to.
            """
            queryset._add_hints(instance=self.instance)
            if self._db:
                queryset = queryset.using(self._db)
            queryset = queryset.filter(**self.core_filters)
            queryset._known_related_objects = {
                self.field: {self.instance.pk: self.instance}
            }
            return queryset

        def _remove_prefetched_objects(self):
            try:
                self.instance._prefetched_objects_cache.pop(
                    self.field.relationship_related_query_name()
                )
            except (AttributeError, KeyError):
                pass  # nothing to clear from cache

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[
                    self.field.relationship_related_query_name()
                ]
            except (AttributeError, KeyError):
                queryset = super(RelationshipManager, self).get_queryset()
                return self._apply_rel_filters(queryset)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super(RelationshipManager, self).get_queryset()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)

            query = {"%s__in" % self.field.name: instances}
            queryset = queryset._next_is_sticky().filter(**query)

            # For non-autocreated 'through' models, can't assume we are
            # dealing with PK values.
            pk = rel.model._meta.pk

            # table_map here contains a map of tables to used aliases - in the case
            # that this is a recursive relationship we want the most recent alias,
            # i.e. the joined table, not the base table.
            join_table = queryset.query.table_map[pk.model._meta.db_table][-1]
            connection = connections[queryset.db]
            qn = connection.ops.quote_name
            queryset = queryset.extra(
                select={
                    "_prefetch_related_val_%s"
                    % f.attname: "%s.%s"
                    % (qn(join_table), qn(f.column))
                    for f in [pk]
                }
            )

            def rel_obj_attr(result):
                return tuple(
                    getattr(result, "_prefetch_related_val_%s" % f.attname)
                    for f in [pk]
                )

            def instance_attr(inst):
                return tuple(
                    f.get_db_prep_value(getattr(inst, f.attname), connection)
                    for f in [pk]
                )

            if not self.field.multiple:
                instances_dict = {instance_attr(inst): inst for inst in instances}
                for rel_obj in queryset:
                    instance = instances_dict[rel_obj_attr(rel_obj)]
                    setattr(rel_obj, self.field.name, instance)

            return (
                queryset,
                rel_obj_attr,
                instance_attr,
                False,
                self.field.relationship_related_query_name(),
            ) + ((False,) if django.VERSION[0] >= 2 else ())

        # All of the standard data-modifying methods are not supported by Relationship
        def add(self, *args, **kwargs):
            raise NotImplementedError

        def create(self, *args, **kwargs):
            raise NotImplementedError

        def get_or_create(self, *args, **kwargs):
            raise NotImplementedError

        def update_or_create(self, *args, **kwargs):
            raise NotImplementedError

        def remove(self, *args, **kwargs):
            raise NotImplementedError

        def clear(self, *args, **kwargs):
            raise NotImplementedError

        def set(self, *args, **kwargs):
            raise NotImplementedError

    return RelationshipManager


class CustomForeignObjectRel(ForeignObjectRel):
    """
    Define some extra Field methods so this Rel acts more like a Field, which
    lets us use ReverseManyToOneDescriptor in both directions.
    """

    def __init__(self, *args, **kwargs):
        super(CustomForeignObjectRel, self).__init__(*args, **kwargs)
        self.multiple = self.field.reverse_multiple
        self.reverse_multiple = self.field.multiple

    @property
    def foreign_related_fields(self):
        return []

    @property
    def local_related_fields(self):
        return []

    def get_attname(self):
        return self.name

    def relationship_related_query_name(self):
        return self.remote_field.name

    def get_extra_restriction(self, where_class, alias, related_alias):
        return Restriction(
            forward=False,
            local_model=self.related_model,
            related_model=self.model,
            local_alias=related_alias,
            related_alias=alias,
            predicate=self.field.predicate,
            where_class=where_class,
        )

    def get_forward_related_filter(self, obj):
        """
        Return the filter arguments which select the instances of self.model
        that are related to obj.
        """
        q = self.field.predicate

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


class ManyToManyRelationshipDescriptor(ReverseManyToOneDescriptor):

    @cached_property
    def related_manager_cls(self):
        related_model = self.rel.related_model

        manager = create_relationship_many_manager(
            related_model._default_manager.__class__, self.rel
        )

        return manager


class Relationship(models.ForeignObject):
    """
    This is a Django model field.
    """

    auto_created = False

    many_to_many = False
    many_to_one = False
    one_to_many = False
    one_to_one = False

    rel_class = CustomForeignObjectRel

    def __init__(self, to, predicate, **kwargs):
        self.multiple = kwargs.pop("multiple", True)
        self.reverse_multiple = kwargs.pop("reverse_multiple", True)
        if self.multiple and self.reverse_multiple:
            self.accessor_class = ManyToManyRelationshipDescriptor
            self.related_accessor_class = ManyToManyRelationshipDescriptor
        else:
            if self.multiple:
                self.accessor_class = ManyToManyRelationshipDescriptor
            else:
                self.accessor_class = ReverseOneToOneDescriptor
            if self.reverse_multiple:
                self.related_accessor_class = ManyToManyRelationshipDescriptor
            else:
                self.related_accessor_class = ReverseOneToOneDescriptor

        kwargs.setdefault("on_delete", models.DO_NOTHING)
        kwargs.setdefault("from_fields", [])
        kwargs.setdefault("to_fields", [])
        super(Relationship, self).__init__(to, **kwargs)
        self.predicate = predicate

    def deconstruct(self):
        name, path, args, kwargs = super(Relationship, self).deconstruct()
        kwargs["predicate"] = self.predicate
        return name, path, args, kwargs

    @property
    def field(self):
        """
        Makes ReverseManyToOneDescriptor work in both directions.
        """
        return self.remote_field

    def get_accessor_name(self):
        return self.name

    def get_extra_restriction(self, where_class, related_alias, local_alias):
        return Restriction(
            forward=True,
            local_model=self.model,
            related_model=self.related_model,
            local_alias=local_alias,
            related_alias=related_alias,
            predicate=self.predicate,
            where_class=where_class,
        )

    def get_forward_related_filter(self, obj):
        """
        Return the filter arguments which select the instances of self.model
        that are related to obj.
        """
        q = self.field.predicate

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
        # kwargs['virtual_only'] = True
        super(ForeignObject, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.accessor_class(self))

    def get_path_info(self, filtered_relation=None):
        if django.VERSION < (2, 0):
            to_opts = self.rel.to._meta
            from_opts = self.model._meta
            return [PathInfo(from_opts, to_opts, (to_opts.pk,), self, True, False)]
        to_opts = self.remote_field.model._meta
        from_opts = self.model._meta
        return [
            PathInfo(
                from_opts, to_opts, (to_opts.pk,), self, True, False, filtered_relation
            )
        ]

    def relationship_related_query_name(self):
        return self.related_query_name()


class L(F):

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        return super(L, self).resolve_expression(
            query._relationship_field_query, allow_joins, reuse, summarize, for_save
        )
