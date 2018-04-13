from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models import Q, F
from django.utils.encoding import python_2_unicode_compatible
from relationships.fields import L, R, Relationship


@python_2_unicode_compatible
class Page(models.Model):
    slug = models.TextField()
    descendants = Relationship(
        'self', Q(slug__startswith=L('slug')),
        related_name='ascendants'
    )

    def __str__(self):
        return self.slug


@python_2_unicode_compatible
class CartItem(models.Model):
    sku = models.CharField(max_length=13)
    description = models.TextField()

    def __str__(self):
        return "Cart item #%s: SKU %s" % (self.pk, self.sku)


@python_2_unicode_compatible
class Product(models.Model):
    sku = models.CharField(max_length=13)
    colour = models.CharField(max_length=20)
    shape = models.CharField(max_length=20)
    size = models.IntegerField()

    cart_items = Relationship(
        CartItem,
        Q(sku=L('sku')),
        related_name='product',
        reverse_multiple=False,
    )

    def __str__(self):
        return "Product #%s: a %s %s, size %s" % (self.sku, self.colour, self.shape, self.size)


@python_2_unicode_compatible
class ProductFilter(models.Model):
    colour = models.CharField(max_length=20)
    size = models.IntegerField()

    products = Relationship(
        Product,
        Q(colour=L('colour')) & Q(size__gte=L('size')),
        related_name='filters',
    )
