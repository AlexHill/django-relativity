from __future__ import unicode_literals

from django.utils.six.moves import zip_longest

from django.test import TestCase
from testapp.models import Category, Categorised, Page, CartItem, Product, ProductFilter


class RelationshipTests(TestCase):

    def assertSeqEqual(self, seq1, seq2):
        MISSING = object()
        for i, (a, b) in enumerate(zip_longest(seq1, seq2, fillvalue=MISSING)):
            if a != b:
                if a is MISSING or b is MISSING:
                    self.fail("Sequences are different lengths")
                else:
                    self.fail("%dth item differs: %s != %s" % (i, a, b))

    @classmethod
    def setUpTestData(cls):
        slugs = [
            'a',
            'a.a.a',
            'a.a.b',
            'a.b',
            'a.b.c',
        ]

        Page.objects.bulk_create(Page(slug=slug) for slug in slugs)

        CartItem.objects.bulk_create([
            CartItem(pk=1, product_code='11', description='red circle'),
            CartItem(pk=2, product_code='22', description='blue triangle'),
            CartItem(pk=3, product_code='11', description='red circle'),
        ])

        Product.objects.bulk_create([
            Product(pk=1, sku='11', psize=4, pcolour='red', pshape='circle'),
            Product(pk=2, sku='22', psize=2, pcolour='blue', pshape='triangle'),
            Product(pk=3, sku='33', psize=3, pcolour='yellow', pshape='square'),
            Product(pk=4, sku='44', psize=1, pcolour='green', pshape='circle'),
            Product(pk=5, sku='55', psize=3, pcolour='red', pshape='triangle'),
            Product(pk=6, sku='66', psize=5, pcolour='blue', pshape='square'),
            Product(pk=7, sku='77', psize=1, pcolour='yellow', pshape='circle'),
            Product(pk=8, sku='88', psize=2, pcolour='green', pshape='triangle'),
            Product(pk=9, sku='99', psize=2, pcolour='red', pshape='square'),
        ])

        Category.objects.bulk_create([
            Category(code='AAA'),
            Category(code='BBB'),
            Category(code='CCC'),
        ])

        Categorised.objects.bulk_create([
            Categorised(pk=1, category_codes='AAA'),
            Categorised(pk=2, category_codes='BBB DDD'),
            Categorised(pk=3, category_codes='AAA CCC'),
            Categorised(pk=4, category_codes='BBB CCC'),
            Categorised(pk=5, category_codes='BBB'),
            Categorised(pk=6, category_codes='CCC'),
        ])

    def test_m2m(self):

        self.assertSeqEqual(
            Category.objects.get(code='AAA').members.all(),
            [
                Categorised.objects.get(pk=1),
                Categorised.objects.get(pk=3),
            ]
        )

        self.assertSeqEqual(
            Categorised.objects.get(pk=4).categories.all(),
            [
                Category.objects.get(code='BBB'),
                Category.objects.get(code='CCC'),
            ]
        )

    def test_m2m_recusive(self):

        ab = Page.objects.get(slug='a.b')

        self.assertSeqEqual(
            ab.descendants.order_by('slug').values_list('slug', flat=True),
            ['a.b', 'a.b.c'],
        )

        self.assertSetEqual(
            set(ab.ascendants.values_list('slug', flat=True)),
            {'a', 'a.b'},
        )

    def test_multiple_conditions(self):

        f = ProductFilter.objects.create(colour='red', size=3)

        self.assertSeqEqual(
            Product.objects.filter(pcolour='red', psize__gte=3).order_by('pk'),
            f.products.order_by('pk'),
        )

        self.assertSeqEqual(
            Product.objects.filter(filters=f),
            Product.objects.filter(pcolour='red', psize__gte=3).order_by('pk'),
        )

        self.assertSeqEqual(
            Product.objects.filter(pcolour='red', psize__gte=3).first().filters.all(),
            [f],
        )

    def test_multi_hop(self):
        f = ProductFilter.objects.create(colour='red', size=3)

        cart_items = CartItem.objects.filter(product_code__in=Product.objects.filter(pcolour='red', psize__gte=3).values_list('sku', flat=True)).order_by('pk')
        self.assertSeqEqual(
            cart_items,
            CartItem.objects.filter(product__filters=f),
        )

        self.assertSeqEqual(
            ProductFilter.objects.filter(products__cart_items=cart_items),
            [f],
        )

    def test_m2o_forward_accessor(self):
        self.assertEqual(
            CartItem.objects.get(pk=1).product,
            Product.objects.get(pk=1),
        )

    def test_m2o_reverse_accessor(self):
        self.assertSeqEqual(
            Product.objects.get(pk=1).cart_items.all().order_by('pk'),
            CartItem.objects.filter(product_code='11').order_by('pk'),
        )

    def test_m2o_forward_filter(self):
        self.assertSeqEqual(
            Product.objects.filter(cart_items__description='red circle').distinct(),
            [Product.objects.get(pk=1)]
        )

    def test_m2o_reverse_filter(self):
        self.assertSeqEqual(
            CartItem.objects.filter(product__pcolour='red', product__pshape='circle'),
            [CartItem.objects.get(pk=1), CartItem.objects.get(pk=3)]
        )
