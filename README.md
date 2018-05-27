# django-relativity

django-relativity provides a `Relationship` field that lets you describe non-foreign-key relationships between your models and use them throughout the ORM.

_Non-foreign-key relationships?_

Like the relationship between a node and its descendants in a tree, or between two tagged items that share a tag. Almost anything you can express with Django's filter syntax, you can use to define a relationship.

_Use them throughout the ORM?_

Yes, across joins, in filters, in methods like `prefetch_related()` or `values()` - anywhere Django expects to see a field.

## What does the code look like?

Here's are some models for an imaginary website about chemistry, where users can filter compounds by regular expression and save their searches:

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
        predicate=Q(product_code=L('sku')),
        multiple=False,
    )
```

## What state is this project in?

This project is in active development. Feel free to try it out. Things not covered by the tests have every chance of not working.