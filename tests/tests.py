from __future__ import unicode_literals

from unittest import expectedFailure

from django.test import TestCase

from .models import (
    CartItem,
    Categorised,
    Category,
    MPTTPage,
    Page,
    Product,
    ProductFilter,
    TBMPPage,
    TBNSPage,
    SavedFilter,
    User,
    LinkedNode,
    UserGenerator,
)


class RelationshipTests(TestCase):
    def assertSeqEqual(self, seq1, seq2):
        self.assertSequenceEqual(list(seq1), list(seq2))

    @classmethod
    def setUpTestData(cls):
        slugs = [
            "Top",
            "Top.Collections",
            "Top.Collections.Pictures",
            "Top.Collections.Pictures.Astronomy",
            "Top.Collections.Pictures.Astronomy.Astronauts",
            "Top.Collections.Pictures.Astronomy.Galaxies",
            "Top.Collections.Pictures.Astronomy.Stars",
            "Top.Hobbies",
            "Top.Hobbies.Amateurs_Astronomy",
            "Top.Science",
            "Top.Science.Astronomy",
            "Top.Science.Astronomy.Astrophysics",
            "Top.Science.Astronomy.Cosmology",
        ]

        mptt_cache = {}
        tbmp_cache = {}
        tbns_cache = {}
        slug_tuples = (tuple(s.split(".")) for s in slugs)
        for i, slug in enumerate(sorted(slug_tuples, key=len)):

            kwargs = {"name": slug[-1], "slug": ".".join(slug)}
            mptt_cache[slug] = MPTTPage.objects.create(
                parent=mptt_cache.get(slug[:-1]), **kwargs
            )

            tbmp_parent = tbmp_cache.get(slug[:-1])
            tbmp_cache[slug] = (
                tbmp_parent.add_child(**kwargs)
                if tbmp_parent
                else TBMPPage.add_root(**kwargs)
            )

            tbns_parent = tbns_cache.get(slug[:-1])
            if tbns_parent:
                tbns_parent.refresh_from_db()
            tbns_cache[slug] = (
                tbns_parent.add_child(**kwargs)
                if tbns_parent
                else TBNSPage.add_root(**kwargs)
            )

            Page.objects.create(**kwargs)

        CartItem.objects.bulk_create(
            [
                CartItem(pk=1, product_code="11", description="red circle"),
                CartItem(pk=2, product_code="22", description="blue triangle"),
                CartItem(pk=3, product_code="11", description="red circle"),
            ]
        )

        Product.objects.bulk_create(
            [
                Product(pk=1, sku="11", size=4, colour="red", shape="circle"),
                Product(pk=2, sku="22", size=2, colour="blue", shape="triangle"),
                Product(pk=3, sku="33", size=3, colour="yellow", shape="square"),
                Product(pk=4, sku="44", size=1, colour="green", shape="circle"),
                Product(pk=5, sku="55", size=3, colour="red", shape="triangle"),
                Product(pk=6, sku="66", size=5, colour="blue", shape="square"),
                Product(pk=7, sku="77", size=1, colour="yellow", shape="circle"),
                Product(pk=8, sku="88", size=2, colour="green", shape="triangle"),
                Product(pk=9, sku="99", size=2, colour="red", shape="square"),
            ]
        )

        Category.objects.bulk_create(
            [
                Category(pk=1, code="AAA"),
                Category(pk=2, code="BBB"),
                Category(pk=3, code="CCC"),
            ]
        )

        Categorised.objects.bulk_create(
            [
                Categorised(pk=1, category_codes="AAA"),
                Categorised(pk=2, category_codes="BBB DDD"),
                Categorised(pk=3, category_codes="AAA CCC"),
                Categorised(pk=4, category_codes="BBB CCC"),
                Categorised(pk=5, category_codes="BBB"),
                Categorised(pk=6, category_codes="CCC"),
            ]
        )

    def test_m2m_accessor_forward(self):
        self.assertSeqEqual(
            Category.objects.get(code="AAA").members.all(),
            [Categorised.objects.get(pk=1), Categorised.objects.get(pk=3)],
        )

    def test_m2m_accessor_reverse(self):
        self.assertSeqEqual(
            Categorised.objects.get(pk=4).categories.all(),
            [Category.objects.get(code="BBB"), Category.objects.get(code="CCC")],
        )

    def test_m2m_filter_forward(self):
        self.assertSeqEqual(
            Category.objects.filter(members__pk__in=[4, 6]).distinct().order_by("pk"),
            Category.objects.filter(pk__in=[2, 3]).order_by("pk"),
        )

    # TODO: fix this or make it break loudly
    @expectedFailure
    def test_m2m_exclude_forward(self):
        self.assertSeqEqual(
            Category.objects.exclude(members__pk__in=[4, 6]).distinct().order_by("pk"),
            Category.objects.exclude(pk__in=[2, 3]).order_by("pk"),
        )

    def test_m2m_filter_reverse(self):
        self.assertSeqEqual(
            Categorised.objects.filter(categories__pk__in=[1, 3])
            .distinct()
            .order_by("pk"),
            Categorised.objects.filter(pk__in=[1, 3, 4, 6]).order_by("pk"),
        )

    def test_m2m_prefetch_related_forward(self):
        member_qs = Categorised.objects.filter(pk__lte=4)
        with self.assertNumQueries(2):
            members = member_qs.prefetch_related("categories")
            member_dict = {m: list(m.categories.all()) for m in members}
        self.assertDictEqual(
            member_dict, {m: list(m.categories.all()) for m in member_qs}
        )

    def test_m2m_prefetch_related_reverse(self):
        category_qs = Category.objects.filter(code__in=["AAA", "BBB"])
        with self.assertNumQueries(2):
            categories = category_qs.prefetch_related("members")
            category_dict = {c: list(c.members.all()) for c in categories}
        self.assertDictEqual(
            category_dict, {c: list(c.members.all()) for c in category_qs}
        )

    def test_m2m_recursive_accessor_forward(self):
        def test_for(page_model):
            p = page_model.objects.get(slug="Top.Science.Astronomy")
            self.assertSeqEqual(
                p.descendants.values_list("slug", flat=True).order_by("slug"),
                [
                    "Top.Science.Astronomy.Astrophysics",
                    "Top.Science.Astronomy.Cosmology",
                ],
            )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2m_recursive_accessor_reverse(self):
        def test_for(page_model):
            p = page_model.objects.get(slug="Top.Science.Astronomy")
            self.assertSeqEqual(
                p.rootpath.values_list("slug", flat=True).order_by("slug"),
                ["Top", "Top.Science", "Top.Science.Astronomy"],
            )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2m_recursive_filter_forward(self):
        def test_for(page_model):
            self.assertSeqEqual(
                page_model.objects.filter(subtree__slug__contains="Stars")
                .values_list("slug", flat=True)
                .distinct()
                .order_by("slug"),
                [
                    "Top",
                    "Top.Collections",
                    "Top.Collections.Pictures",
                    "Top.Collections.Pictures.Astronomy",
                    "Top.Collections.Pictures.Astronomy.Stars",
                ],
            )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2m_recursive_filter_reverse(self):
        def test_for(page_model):
            self.assertSeqEqual(
                page_model.objects.filter(ascendants__slug__contains="Astronomy")
                .values_list("slug", flat=True)
                .distinct()
                .order_by("slug"),
                [
                    "Top.Collections.Pictures.Astronomy.Astronauts",
                    "Top.Collections.Pictures.Astronomy.Galaxies",
                    "Top.Collections.Pictures.Astronomy.Stars",
                    "Top.Science.Astronomy.Astrophysics",
                    "Top.Science.Astronomy.Cosmology",
                ],
            )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2m_recursive_prefetch_related_forward(self):
        def test_for(page_model):
            qs = page_model.objects.filter(slug__startswith="Top.Science")
            with self.assertNumQueries(2 + qs.count()):
                pages = qs.prefetch_related("descendants")
                for page in pages:
                    self.assertEqual(
                        list(page.descendants.all()),
                        list(page_model.objects.filter(ascendants=page)),
                    )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2m_recursive_prefetch_related_reverse(self):
        def test_for(page_model):
            qs = page_model.objects.filter(slug__startswith="Top.Science")
            with self.assertNumQueries(2 + qs.count()):
                pages = qs.prefetch_related("rootpath")
                for page in pages:
                    self.assertEqual(
                        list(page.rootpath.all()),
                        list(page_model.objects.filter(subtree=page)),
                    )

        test_for(Page)
        test_for(MPTTPage)
        test_for(TBMPPage)
        test_for(TBNSPage)

    def test_m2o_accessor_forward(self):
        self.assertEqual(CartItem.objects.get(pk=1).product, Product.objects.get(pk=1))

    def test_m2o_accessor_reverse(self):
        self.assertSeqEqual(
            Product.objects.get(pk=1).cart_items.all().order_by("pk"),
            CartItem.objects.filter(product_code="11").order_by("pk"),
        )

    def test_m2o_filter_reverse(self):
        self.assertSeqEqual(
            Product.objects.filter(cart_items__description="red circle").distinct(),
            [Product.objects.get(pk=1)],
        )

    def test_m2o_filter_forward(self):
        self.assertSeqEqual(
            CartItem.objects.filter(product__colour="red", product__shape="circle"),
            [CartItem.objects.get(pk=1), CartItem.objects.get(pk=3)],
        )

    def test_m2o_prefetch_related_forward(self):
        with self.assertNumQueries(2):
            products = (
                Product.objects.filter(colour="red")
                .prefetch_related("cart_items")
                .all()
            )
            for product in products:
                for cart_item in product.cart_items.all():
                    self.assertEqual(cart_item.product, product)

    def test_m2o_reverse_select_related(self):
        with self.assertNumQueries(1):
            for cart_item in CartItem.objects.select_related("product").all():
                self.assertEqual(cart_item.product.sku, cart_item.product_code)

    def test_multi_hop(self):
        f = ProductFilter.objects.create(fcolour="red", fsize=3)

        cart_items = CartItem.objects.filter(
            product_code__in=Product.objects.filter(
                colour="red", size__gte=3
            ).values_list("sku", flat=True)
        ).order_by("pk")

        self.assertSeqEqual(cart_items, CartItem.objects.filter(product__filters=f))

        self.assertSeqEqual(
            ProductFilter.objects.filter(products__cart_items__in=cart_items), [f, f]
        )

    def test_m2m(self):
        users = User.objects.bulk_create(
            User(pk=uid, username="User %d" % uid) for uid in range(1, 4)
        )

        sf = SavedFilter.objects.bulk_create(
            [
                SavedFilter(pk=1, user=users[0], search_regex="a"),
                SavedFilter(pk=2, user=users[1], search_regex="a"),
                SavedFilter(pk=3, user=users[0], search_regex="a"),
            ]
        )

        self.assertSeqEqual(
            User.objects.filter(savedfilter__pk__in=[1, 2]),
            User.objects.filter(pk__in=[1, 2]),
        )

        self.assertSeqEqual(
            User.objects.exclude(savedfilter__pk__in=[1, 2]),
            User.objects.exclude(pk__in=[1, 2]),
        )

    def test_single_reverse(self):
        node_1 = LinkedNode.objects.create(
            name="first node",
            prev_id=None,
        )
        node_2 = LinkedNode.objects.create(
            name="next node",
            prev_id=node_1.id,
        )
        node_3 = LinkedNode.objects.create(
            name="last node",
            prev_id=node_2.id,
        )
        self.assertEqual(node_3.prev, node_2)
        self.assertEqual(node_1.next, node_2)

        self.assertIsNone(node_3.next)
        self.assertIsNone(node_1.prev)

    def test_not_nullable(self):
        item = CartItem.objects.create(
            pk=4,
            product_code="nonexistent",
            description="cart item for anonexistent product",
        )
        with self.assertRaises(Product.DoesNotExist):
            item.product

    def test_complex_expression(self):
        ug = UserGenerator.objects.create()
        self.assertEqual(ug.user, User.objects.get(username="generated_for_%d" % ug.id))

    def test_descriptor_not_cached(self):
        item = CartItem.objects.first()
        self.assertIsNotNone(item.product)

        item.product.delete()
        with self.assertRaises(Product.DoesNotExist):
            item.product
