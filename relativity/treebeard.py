from django.db.models import Q

from relativity.fields import Relationship, L


class MP_Descendants(Relationship):

    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "ascendants")
        kwargs.update({
            "to": "self",
            "predicate": Q(path__startswith=L("path"), path__ne=L("path")),
        })
        super(MP_Descendants, self).__init__(**kwargs)


class MP_Subtree(Relationship):

    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "rootpath")
        kwargs.update({
            "to": "self",
            "predicate": Q(path__startswith=L("path")),
        })
        super(MP_Subtree, self).__init__(**kwargs)


class NS_Descendants(Relationship):

    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "ascendants")
        kwargs.update({
            "to": "self",
            "predicate": Q(
                tree_id=L("tree_id"),
                lft__gt=L("lft"),
                lft__lt=L("rgt"),
            ),
        })
        super(NS_Descendants, self).__init__(**kwargs)


class NS_Subtree(Relationship):

    def __init__(self, **kwargs):
        kwargs.setdefault("related_name", "rootpath")
        kwargs.update({
            "to": "self",
            "predicate": Q(
                tree_id=L("tree_id"),
                lft__gte=L("lft"),
                lft__lt=L("rgt"),
            ),
        })
        super(NS_Subtree, self).__init__(**kwargs)
