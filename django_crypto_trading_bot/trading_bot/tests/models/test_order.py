import unittest
from decimal import Decimal

import pytest

from django_crypto_trading_bot.trading_bot.models import Account, Market, Order

from ..factories import (
    AccountFactory,
    MarketFactory,
    OrderFactory,
    OrderFactoryDifferentMarket,
    OrderFactoryNew,
)


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

    def test_last_order(self):
        market: Market = MarketFactory()
        account: Account = AccountFactory()

        # test without any market
        assert Order.last_order(market=market, account=account) is None
        assert Order.last_order(account=account) is None

        # test with single order
        order: Order = OrderFactory()
        assert Order.last_order(market=market, account=account) == order
        assert Order.last_order(account=account) == order

        # test with different market
        order_different_market: Order = OrderFactoryDifferentMarket()
        assert Order.last_order(account=account) == order_different_market
        assert Order.last_order(market=market, account=account) == order

        # test with newer order
        order_new: Order = OrderFactoryNew()
        assert Order.last_order(account=account) == order_new
        assert Order.last_order(market=market, account=account) == order_new
