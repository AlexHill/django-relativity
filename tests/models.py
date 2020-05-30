from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models import Lookup, Q
from django.db.models.fields import Field
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from six import python_2_unicode_compatible
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

from relativity.fields import L, Relationship
from relativity.mptt import MPTTDescendants, MPTTSubtree
from relativity.treebeard import MP_Descendants, NS_Descendants, MP_Subtree, NS_Subtree


class LinkedNode(models.Model):
    name = models.CharField(max_length=30)
    prev_id = models.IntegerField(null=True)

    next = Relationship(
        "self",
        predicate=Q(prev_id=L('id')),
        reverse_multiple=False,
        multiple=False,
        related_name="prev",
    )


@Field.register_lookup
class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s" % (lhs, rhs), params


@python_2_unicode_compatible
class BasePage(models.Model):
    name = models.TextField()
    slug = models.CharField(unique=True, null=False, blank=False, max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class MPTTPage(MPTTModel, BasePage):
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    descendants = MPTTDescendants()
    subtree = MPTTSubtree()


class TBMPPage(MP_Node, BasePage):

    descendants = MP_Descendants()
    subtree = MP_Subtree()


class TBNSPage(NS_Node, BasePage):

    descendants = NS_Descendants()
    subtree = NS_Subtree()


@python_2_unicode_compatible
class PageBase(BasePage):
    descendants = Relationship(
        "self",
        Q(slug__startswith=L("slug"), slug__ne=L("slug")),
        related_name="ascendants",
    )

    subtree = Relationship(
        "self", Q(slug__startswith=L("slug")), related_name="rootpath"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Page(PageBase):
    pass


class Categorised(models.Model):
    category_codes = models.TextField()


@python_2_unicode_compatible
class CategoryBase(models.Model):
    code = models.CharField(unique=True, max_length=255)
    members = Relationship(
        Categorised, Q(category_codes__contains=L("code")), related_name="categories",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return "Category #%d: %s" % (self.pk, self.code)


class Category(CategoryBase):
    pass


@python_2_unicode_compatible
class Product(models.Model):
    sku = models.CharField(max_length=13)
    colour = models.CharField(max_length=20)
    shape = models.CharField(max_length=20)
    size = models.IntegerField()

    def __str__(self):
        return "Product #%s: a %s %s, size %s" % (
            self.sku,
            self.colour,
            self.shape,
            self.size,
        )


@python_2_unicode_compatible
class CartItem(models.Model):
    product_code = models.CharField(max_length=13)
    description = models.TextField()

    product = Relationship(
        Product, Q(sku=L("product_code")), related_name="cart_items", multiple=False
    )

    def __str__(self):
        return "Cart item #%s: SKU %s" % (self.pk, self.sku)


@python_2_unicode_compatible
class ProductFilter(models.Model):
    fcolour = models.CharField(max_length=20)
    fsize = models.IntegerField()

    products = Relationship(
        Product, Q(colour=L("fcolour"), size__gte=L("fsize")), related_name="filters"
    )

    cartitems = Relationship(
        CartItem,
        Q(product__colour=L("fcolour"), product__size__gte=L("fsize")),
        related_name="filters",
    )

    def __str__(self):
        return "ProductFilter #%d: %s size %s" % (self.pk, self.fcolour, self.fsize)


@python_2_unicode_compatible
class User(models.Model):
    username = models.CharField(primary_key=True, max_length=255)

    def __str__(self):
        return self.username


@python_2_unicode_compatible
class Chemical(models.Model):
    formula = models.TextField()
    chemical_name = models.TextField()
    common_name = models.TextField(blank=True)

    def __str__(self):
        return self.formula


class SavedFilter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_regex = models.TextField()
    chemicals = Relationship(Chemical, Q(formula__regex=L("search_regex")))
