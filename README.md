# django-relativity

[![PyPI](https://img.shields.io/pypi/v/django-relativity.svg)](https://pypi.org/project/django-relativity/)
[![Build Status](https://travis-ci.org/AlexHill/django-relativity.svg?branch=master)](https://travis-ci.org/AlexHill/django-relativity)

django-relativity provides a `Relationship` field that lets you declare the non-foreign-key relationships between your models and use them throughout the ORM.

_Non-foreign-key relationships?_

Like the relationship between a node and its descendants in a tree, or between two tagged items that share a tag. Almost anything you can express with Django's filter syntax, you can use to define a relationship.

_Use them throughout the ORM?_

Yes, across joins, in `filter()`, in methods like `prefetch_related()` or `values()` - anywhere Django expects to see a field.

## What problem does this solve?

Sometimes the relationships between our models are more complex than equality between a primary key field on one model and a foreign key on another.

For example: when working with trees, we very often need to find a given node's descendants - its children, their children, and so on. The exact query we have to run depends on how we've chosen to implement our tree structure at the database level, and fortunately there are mature libraries available to take care of that for us. [django-mptt](http://django-mptt.readthedocs.io/en/latest/models.html#get-descendants-include-self-false) and [django-treebeard](http://django-treebeard.readthedocs.io/en/latest/api.html#treebeard.models.Node.get_descendants) both provide methods called `get_descendants()` for exactly this purpose. These return a queryset selecting the node's descendants, which we can then filter further, or use as an argument to another filter, and so on. So what's the problem?

The problem is that the node-descendants relationship is invisible to the Django ORM. We can't filter against it, like `Node.objects.filter(descendants__in=objs)`. We can't traverse it, like `Node.objects.filter(descendants__name__startswith="A")`. We can't prefetch it. None of the niceties that Django provides for working with relationships are available for us to use with this relationship, because it can't be declared as a `ManyToManyField` or `ForeignKey`.

django-relativity lets all those ORM features work with almost any kind of relationship you can dream up.

### MPTT and treebeard helpers

If you use django-mptt or django-treebeard and you want to jump right in, relativity comes with fields to select a node's descendants and its subtree (which respectively exclude and include the current node). The default reverse relation names for these fields are `ascendants` and `rootpath`.

```python
# For django-mptt
from relativity.mptt import MPTTDescendants, MPTTSubtree

# for treebeard with materialised path
from relativity.treebeard import MP_Descendants, MP_Subtree

# for treebeard with nested sets
from relativity.treebeard import NS_Descendants, NS_Subtree


class TreeNode(MPTTModel):
    ...
    
    # after defining all your other fields, including TreeForeignKey...
    descendants = MPTTDescendants()
    subtree = MPTTSubtree()
```

## What does the code look like?

Here are some models for an imaginary website about chemistry, where users can filter compounds by regular expression and save their searches:

```python
from relativity.fields import L, Relationship

class Chemical(Model):
    common_name = TextField()
    chemical_name = TextField()
    formula = TextField()

class SavedFilter(Model):
    user = ForeignKey(User)
    search_regex = TextField()
    chemicals = Relationship(
        to=Chemical,
        predicate=Q(formula__regex=L('search_regex')),
    )
```

Now I can use that field like this:

```python
my_filter.chemicals.all()  # all the chemicals whose formulae match this filter
my_chemical.saved_filters.all()  # all the filters whose regexps match this chemical
my_user.filter(saved_filters__chemicals=my_chemical)  # users with filters matching this chemical
my_chemical.filter(saved_filters__user=my_user)  # chemicals in any of this user's filters
```

In short, I can use it just like a normal Django relation. It provides forward and reverse properties that return Managers, and I can use it in filters spanning multiple models.

_How does that `Relationship` field work?_

A `Relationship` behaves like a `ForeignKey` or `ManyToManyField` and defines a relationship with another model. Unlike the built-in Django relations, `Relationship` doesn't use its own database column or table to determine which instances are related. Instead, you give it an arbitrary _predicate_, expressed as a normal Django `Q`, which determines which instances of the `to` model are in the relationship.

_What's that `L` doing there?_

In Django ORM expressions, `F` is a reference to a field on the model being queried. `L` is similar, but refers to a field on the model on which the `Relationship` is defined. Think of it as L for the _left-hand_ side of a join, or L for the _local_ model.

Going back to our example - the `chemicals` field provides the set of `Chemical`s whose formulae match the `SavedFilter`'s regular expression.

Let's make some chemicals:

```python
>>> Chemical.objects.create(name="baking soda", formula="NaHCO3")
... Chemical.objects.create(common_name="freon",  formula="CF2Cl2")
... Chemical.objects.create(common_name="grain alcohol", formula="C2H5OH")
... Chemical.objects.create(common_name="quartz", formula="SiO2")
... Chemical.objects.create(common_name="salt", formula="NaCl")
```

Now, say I'm a user who's interested in chemicals containing chlorine. Simple enough:

```python
>>> chloriney = SavedFilter.objects.create(user=alex, search_regex=r'Cl')
>>> chloriney.compounds.all()
<QuerySet [<Chemical: CF2Cl2>, <Chemical: NaCl>]>
```

Anne is interested in oxides, so her regex is a bit more complicated:

```python
>>> oxides = SavedFilter.objects.create(user=anne, search_regex=r'([A-Z][a-z]?\d*)O(\d+|(?!H))')
>>> oxides.compounds.all()
<QuerySet [<Chemical: NaHCO3>, <Chemical: SiO2>]>
```

Now, this is nothing you couldn't do with a helper method on `SavedFilter` which returns the appropriate QuerySet. But now we add a new chemical to our database, and we want to identify users who are interested in that chemical so we can notify them:

```python
>>> added_chemical = Chemical.objects.create(common_name="chlorine dioxide", chemical_name="chlorine dioxide", formula="ClO2")
<Chemical: ClO2>
>>> User.objects.filter(saved_filters__chemicals=added_chemical)
<QuerySet [<User: alex>, <User: anne>]>
```

This is why I call django-relativity a _force-multiplier_ for the ORM. `Relationship`s work with the ORM just like `ForeignKey`s or `ManyToManyField`s. You can traverse them and filter on them just like you can with the built-in relationship fields. The goal of django-relativity is for `Relationship`s to be able to do anything a normal Django relationship field can do.

### Reverse relations

`Relationship`s work in the reverse direction as well, with the same naming behaviour as Django's fields: the default related name is `<model_name>_set` or `<model_name>` depending on arity, overridable with the `related_name` argument. `related_query_name` works as well.

In the example above, `my_chemical.saved_filter_set.all()` will return all of the `SavedFilter`s matching `my_chemical`. `Chemical.objects.filter(saved_filters__user=alex)` will select all of the chemicals in all of my saved filters.

### Arity

Relationships between models can be one-to-one, one-to-many, many-to-one, or many-to-many. `Relationship` can express all of those, using the `multiple` and `reverse_multiple` arguments. Both default to `True`.

Here's a many-to-one example - many cart items can be associated with each product, but only one product is associated with each cart item.

```python
class CartItem(models.Model):
    product_code = models.TextField()
    product = Relationship(
        to=Product,
        predicate=Q(sku=L('product_code')),
        multiple=False,
    )
```

## What state is this project in?

This project is used in production and in active development. Things not covered by the tests have every chance of not working.


## Migrating from relativity < 0.2.0

Before 0.2.0, it was necessary to import a backported version of `django.db.models.Q` from `relativity.compat` in order to make migrations work in Django 1.11. From 0.2.0 onwards, that's no longer necessary. The backported `Q` still exists as an alias to django.db.models, but a DeprecationWarning will be issued on import. You should replace all uses with Django's standard `Q`.

From 0.2.0 onwards, relativity's fields do not generate migrations. When migrating from older versions, I recommend simply removing all references to relativity's fields from the original migrations that created them, rather than generating new migrations removing the virtual fields.
