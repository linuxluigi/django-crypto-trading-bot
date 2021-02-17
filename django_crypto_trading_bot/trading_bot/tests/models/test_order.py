import unittest
from datetime import datetime
from decimal import Decimal

import pytest
from pytz import UTC

from django_crypto_trading_bot.trading_bot.models import Account, Market, Order, Trade
from django_crypto_trading_bot.trading_bot.models.choices import (
    OrderSide,
    OrderStatus,
    OrderType,
)

from ..factories import (
    AccountFactory,
    EthBtcMarketFactory,
    MarketFactory,
    OrderFactory,
    OrderFactoryDifferentMarket,
    OrderFactoryNew,
)
from ..fixtures import order_dict


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

    def test_get_or_create_by_api_response_create_order(self):
        account: Account = AccountFactory()
        market: Market = EthBtcMarketFactory()
        order: Order = Order.get_or_create_by_api_response(
            cctx_order=order_dict(), account=account
        )

        assert order.account == account
        assert order.market == market
        assert order.order_id == "12345-67890:09876/54321"
        assert order.status == OrderStatus.OPEN
        assert order.timestamp == datetime(
            year=2017,
            month=8,
            day=17,
            hour=9,
            minute=42,
            second=26,
            microsecond=216000,
            tzinfo=UTC,
        )
        assert order.order_type == OrderType.LIMIT
        assert order.side == OrderSide.BUY
        self.assertAlmostEqual(order.price, Decimal.from_float(0.06917684), 8)
        self.assertAlmostEqual(order.amount, Decimal.from_float(1.5), 8)
        self.assertAlmostEqual(order.filled, Decimal.from_float(1.1), 8)

        # check if there trade was added
        assert Trade.objects.filter(order=order).count() == 2

        # get order from database
        assert order == Order.objects.get(pk=order.pk)

    def test_get_or_create_by_api_response_update_order(self):
        account: Account = AccountFactory()
        EthBtcMarketFactory()
        order_original: Order = OrderFactory()
        order_update: Order = Order.get_or_create_by_api_response(
            cctx_order=order_dict(order_id=order_original.order_id), account=account
        )

        # check for updated properties
        self.assertAlmostEqual(order_update.filled, Decimal.from_float(1.1), 8)
        assert order_update.status == OrderStatus.OPEN

        # check if order was updated
        assert order_update.pk == order_original.pk

        # check if there trade was added
        assert Trade.objects.filter(order=order_update).count() == 2

        # get order from database
        assert order_update == Order.objects.get(pk=order_update.pk)
