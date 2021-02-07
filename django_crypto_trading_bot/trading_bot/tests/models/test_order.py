import unittest
from decimal import Decimal

import pytest

from django_crypto_trading_bot.trading_bot.models import Order

from ..factories import OrderFactory


@pytest.mark.django_db()
class TestOrder(unittest.TestCase):
    def test_remaining(self):
        order: Order = OrderFactory()

        order.amount = Decimal.from_float(1.5)
        order.filled = Decimal.from_float(0.5)

        assert order.remaining() == Decimal.from_float(1)

    def test_cost(self):
        order: Order = OrderFactory()

        order.price = Decimal.from_float(2)
        order.filled = Decimal.from_float(0.5)

        assert order.cost() == Decimal.from_float(1)

    def test_to_string(self):
        order: Order = OrderFactory()

        order.pk = 1
        order.order_id = "12"

        assert order.__str__() == "1: 12"
