from __future__ import unicode_literals

from django.utils.six.moves import zip_longest

from django.test import TestCase
from testapp.models import Page, CartItem, Product, ProductFilter


class RelationshipTests(TestCase):

    def assertSeqEqual(self, seq1, seq2):
        MISSING = object()
        for i, (a, b) in enumerate(zip_longest(seq1, seq2, fillvalue=MISSING)):
            if a != b:
                if a is MISSING or b is MISSING:
                    self.fail("Sequences are different lengths")
                else:
                    self.fail("%dth item differs: %s != %s" % (i, a, b))

    def setUp(self):
        slugs = [
            'a',
            'a.a.a',
            'a.a.b',
            'a.b',
            'a.b.c',
        ]

        Page.objects.bulk_create(Page(slug=slug) for slug in slugs)

        CartItem.objects.bulk_create([
            CartItem(pk=1, sku='1', description='red circle'),
            CartItem(pk=2, sku='2', description='blue triangle'),
            CartItem(pk=3, sku='1', description='red circle'),
        ])

        Product.objects.bulk_create([
            Product(pk=1, sku='1', size=4, colour='red', shape='circle'),
            Product(pk=2, sku='2', size=2, colour='blue', shape='triangle'),
            Product(pk=3, sku='3', size=3, colour='yellow', shape='square'),
            Product(pk=4, sku='4', size=1, colour='green', shape='circle'),
            Product(pk=5, sku='5', size=3, colour='red', shape='triangle'),
            Product(pk=6, sku='6', size=5, colour='blue', shape='square'),
            Product(pk=7, sku='7', size=1, colour='yellow', shape='circle'),
            Product(pk=8, sku='8', size=2, colour='green', shape='triangle'),
            Product(pk=9, sku='9', size=2, colour='red', shape='square'),
        ])

    def test_relationships(self):

        ab = Page.objects.get(slug='a.b')

        self.assertSeqEqual(
            ab.descendants.order_by('slug').values_list('slug', flat=True),
            ['a.b', 'a.b.c'],
        )

        self.assertSetEqual(
            set(ab.ascendants.values_list('slug', flat=True)),
            {'a', 'a.b'},
        )

    def test_single_forward(self):

        cartitem_1 = CartItem.objects.get(pk=1)
        product_1 = Product.objects.get(pk=1)

        self.assertEqual(cartitem_1.product, product_1)
        self.assertListEqual(
            list(product_1.cart_items.all().order_by('pk')),
            list(CartItem.objects.filter(sku='1').order_by('pk'))
        )

    def test_filter(self):

        self.assertListEqual(
            list(Product.objects.filter(cart_items__description='red circle').distinct()),
            [Product.objects.get(pk=1)]
        )

        self.assertListEqual(
            list(CartItem.objects.filter(product__colour='red', product__shape='circle')),
            [CartItem.objects.get(pk=1), CartItem.objects.get(pk=3)]
        )

    def test_multiple_conditions(self):

        f = ProductFilter.objects.create(colour='red', size=3)

        self.assertSeqEqual(
            Product.objects.filter(colour='red', size__gte=3).order_by('pk'),
            f.products.order_by('pk'),
        )

        self.assertSeqEqual(
            Product.objects.filter(filters=f),
            Product.objects.filter(colour='red', size__gte=3).order_by('pk'),
        )

    def test_multi_hop(self):
        f = ProductFilter.objects.create(colour='red', size=3)

        self.assertSeqEqual(
            CartItem.objects.filter(sku__in=Product.objects.filter(colour='red', size__gte=3)).order_by('pk'),
            CartItem.objects.filter(product__filters=f),
        )
