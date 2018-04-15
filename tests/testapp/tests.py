from __future__ import unicode_literals

from django.test import TestCase
from testapp.models import Category, Categorised, Page, CartItem, Product, ProductFilter


class RelationshipTests(TestCase):

    def assertSeqEqual(self, seq1, seq2):
        self.assertSequenceEqual(list(seq1), list(seq2))

    @classmethod
    def setUpTestData(cls):
        slugs = [
            'Top',
            'Top.Collections',
            'Top.Collections.Pictures',
            'Top.Collections.Pictures.Astronomy',
            'Top.Collections.Pictures.Astronomy.Astronauts',
            'Top.Collections.Pictures.Astronomy.Galaxies',
            'Top.Collections.Pictures.Astronomy.Stars',
            'Top.Hobbies',
            'Top.Hobbies.Amateurs_Astronomy',
            'Top.Science',
            'Top.Science.Astronomy',
            'Top.Science.Astronomy.Astrophysics',
            'Top.Science.Astronomy.Cosmology',
        ]

        Page.objects.bulk_create(Page(pk=i, slug=slug) for i, slug in enumerate(slugs))

        CartItem.objects.bulk_create([
            CartItem(pk=1, product_code='11', description='red circle'),
            CartItem(pk=2, product_code='22', description='blue triangle'),
            CartItem(pk=3, product_code='11', description='red circle'),
        ])

        Product.objects.bulk_create([
            Product(pk=1, sku='11', size=4, colour='red', shape='circle'),
            Product(pk=2, sku='22', size=2, colour='blue', shape='triangle'),
            Product(pk=3, sku='33', size=3, colour='yellow', shape='square'),
            Product(pk=4, sku='44', size=1, colour='green', shape='circle'),
            Product(pk=5, sku='55', size=3, colour='red', shape='triangle'),
            Product(pk=6, sku='66', size=5, colour='blue', shape='square'),
            Product(pk=7, sku='77', size=1, colour='yellow', shape='circle'),
            Product(pk=8, sku='88', size=2, colour='green', shape='triangle'),
            Product(pk=9, sku='99', size=2, colour='red', shape='square'),
        ])

        Category.objects.bulk_create([
            Category(pk=1, code='AAA'),
            Category(pk=2, code='BBB'),
            Category(pk=3, code='CCC'),
        ])

        Categorised.objects.bulk_create([
            Categorised(pk=1, category_codes='AAA'),
            Categorised(pk=2, category_codes='BBB DDD'),
            Categorised(pk=3, category_codes='AAA CCC'),
            Categorised(pk=4, category_codes='BBB CCC'),
            Categorised(pk=5, category_codes='BBB'),
            Categorised(pk=6, category_codes='CCC'),
        ])

    def test_m2m_accessor_forward(self):

        self.assertSeqEqual(
            Category.objects.get(code='AAA').members.all(),
            [
                Categorised.objects.get(pk=1),
                Categorised.objects.get(pk=3),
            ]
        )

    def test_m2m_accessor_reverse(self):
        self.assertSeqEqual(
            Categorised.objects.get(pk=4).categories.all(),
            [
                Category.objects.get(code='BBB'),
                Category.objects.get(code='CCC'),
            ]
        )

    def test_m2m_filter_forward(self):

        self.assertSeqEqual(
            Category.objects.filter(members__pk__in=[4, 6]).distinct().order_by('pk'),
            Category.objects.filter(pk__in=[2, 3]).order_by('pk')
        )

    def test_m2m_filter_reverse(self):
        self.assertSeqEqual(
            Categorised.objects.filter(categories__pk__in=[1, 3]).distinct().order_by('pk'),
            Categorised.objects.filter(pk__in=[1, 3, 4, 6]).order_by('pk'),
        )

    def test_m2m_recursive_accessor_forward(self):
        p = Page.objects.get(slug='Top.Science.Astronomy')
        self.assertSeqEqual(
            p.descendants.values_list('slug', flat=True).order_by('slug'),
            [
                'Top.Science.Astronomy.Astrophysics',
                'Top.Science.Astronomy.Cosmology',
            ],
        )

    def test_m2m_recursive_accessor_reverse(self):
        p = Page.objects.get(slug='Top.Science.Astronomy')
        self.assertSeqEqual(
            p.ascendants.values_list('slug', flat=True).order_by('slug'),
            [
                'Top',
                'Top.Science',
            ],
        )

    def test_m2m_recursive_filter_forward(self):
        self.assertSeqEqual(
            Page.objects.filter(descendants__slug__contains='Stars').values_list('slug', flat=True).distinct().order_by('slug'),
            [
                'Top',
                'Top.Collections',
                'Top.Collections.Pictures',
                'Top.Collections.Pictures.Astronomy',
            ],
        )

    def test_m2m_recursive_filter_reverse(self):
        self.assertSeqEqual(
            Page.objects.filter(ascendants__slug__contains='Astronomy').values_list('slug', flat=True).distinct().order_by('slug'),
            [
                'Top.Collections.Pictures.Astronomy.Astronauts',
                'Top.Collections.Pictures.Astronomy.Galaxies',
                'Top.Collections.Pictures.Astronomy.Stars',
                'Top.Science.Astronomy.Astrophysics',
                'Top.Science.Astronomy.Cosmology',
            ],
        )

    def test_m2o_accessor_forward(self):
        self.assertEqual(
            CartItem.objects.get(pk=1).product,
            Product.objects.get(pk=1),
        )

    def test_m2o_accessor_reverse(self):
        self.assertSeqEqual(
            Product.objects.get(pk=1).cart_items.all().order_by('pk'),
            CartItem.objects.filter(product_code='11').order_by('pk'),
        )

    def test_m2o_filter_reverse(self):
        self.assertSeqEqual(
            Product.objects.filter(cart_items__description='red circle').distinct(),
            [Product.objects.get(pk=1)]
        )

    def test_m2o_filter_forward(self):
        self.assertSeqEqual(
            CartItem.objects.filter(product__colour='red', product__shape='circle'),
            [CartItem.objects.get(pk=1), CartItem.objects.get(pk=3)]
        )

    def test_multiple_conditions(self):

        f = ProductFilter.objects.create(fcolour='red', fsize=3)

        self.assertSeqEqual(
            Product.objects.filter(colour='red', size__gte=3).order_by('pk'),
            f.products.order_by('pk'),
        )

        self.assertSeqEqual(
            Product.objects.filter(filters=f),
            Product.objects.filter(colour='red', size__gte=3).order_by('pk'),
        )

        self.assertSeqEqual(
            Product.objects.filter(colour='red', size__gte=3).first().filters.all(),
            [f],
        )

    def test_multi_hop(self):
        f = ProductFilter.objects.create(fcolour='red', fsize=3)

        cart_items = CartItem.objects.filter(product_code__in=Product.objects.filter(colour='red', size__gte=3).values_list('sku', flat=True)).order_by('pk')
        self.assertSeqEqual(
            cart_items,
            CartItem.objects.filter(product__filters=f),
        )

        self.assertSeqEqual(
            ProductFilter.objects.filter(products__cart_items=cart_items),
            [f],
        )
