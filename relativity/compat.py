import django
from django.db.models.query_utils import Q as DjangoQ


__all__ = ('Q',)

if django.VERSION >= (2,):
    Q = DjangoQ
else:
    class Q(DjangoQ):
        def __init__(self, *args, **kwargs):
            connector = kwargs.pop('_connector', None)
            negated = kwargs.pop('_negated', False)
            super(DjangoQ, self).__init__(children=list(args) + sorted(kwargs.items()), connector=connector, negated=negated)

        def deconstruct(self):
            path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
            args, kwargs = (), {}
            if len(self.children) == 1 and not isinstance(self.children[0], Q):
                child = self.children[0]
                kwargs = {child[0]: child[1]}
            else:
                args = tuple(self.children)
                if self.connector != self.default:
                    kwargs = {'_connector': self.connector}
            if self.negated:
                kwargs['_negated'] = True
            return path, args, kwargs
