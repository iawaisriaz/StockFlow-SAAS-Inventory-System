from decimal import Decimal

from django.test import SimpleTestCase

from products.models import Product


class WeightedAverageCalculationTests(SimpleTestCase):

    def test_opening_stock_and_receipt(self):
        product = Product(
            cost_price=Decimal("3.00"),
            stock_quantity=4,
            inventory_value=Decimal("12.0000"),
        )

        product.recalculate_average()

        self.assertEqual(
            product.average_cost,
            Decimal("3.000000")
        )

        # Simulate receipt arithmetic without DB writes.
        product.inventory_value += (
            Decimal("10") * Decimal("3.50")
        )

        product.stock_quantity += 10
        product.recalculate_average()

        self.assertEqual(
            product.inventory_value,
            Decimal("47.0000")
        )

        self.assertEqual(
            product.stock_quantity,
            14
        )

        self.assertEqual(
            product.average_cost,
            Decimal("3.357143")
        )

    def test_empty_stock_has_zero_value(self):
        product = Product(
            stock_quantity=0,
            inventory_value=Decimal("0.0000"),
        )

        product.recalculate_average()

        self.assertEqual(
            product.average_cost,
            Decimal("0.000000")
        )

        self.assertEqual(
            product.inventory_value,
            Decimal("0.0000")
        )
