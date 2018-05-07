from __future__ import unicode_literals


from django.db.models import Func, Value


class Unaccent(Func):
    function = 'unaccent'

    def __init__(self, text, **extra):
        super(Unaccent, self).__init__(text, **extra)


class Strip(Func):
    function = 'strip'

    def __init__(self, tsvector, **extra):
        super(Strip, self).__init__(tsvector, **extra)


class TSFunc(Func):
    def __init__(self, ts_config, ts_query, **extra):
        super(TSFunc, self).__init__(Value(ts_config), ts_query, **extra)


class ToTSQuery(TSFunc):
    function = 'to_tsquery'


class ToTSVector(TSFunc):
    function = 'to_tsvector'


class ToTSTagsVector(ToTSVector):
    def __init__(self, expression, **extra):
        super(ToTSTagsVector, self).__init__('tags', expression, **extra)


class ToTSTagsQuery(ToTSQuery):
    def __init__(self, expression, **extra):
        super(ToTSTagsQuery, self).__init__('tags', expression, **extra)


class Cast(Func):
    template = '(%(expressions)s)::%(cast_type)s'

    def __init__(self, cast_type, expression, **extra):
        extra['cast_type'] = cast_type
        super(Cast, self).__init__(expression, **extra)
