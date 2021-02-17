import unittest
from datetime import datetime
from decimal import Decimal, getcontext

import pytest
from pytz import UTC

from django_crypto_trading_bot.trading_bot.models import Order, Trade
from django_crypto_trading_bot.trading_bot.models.choices import TakerOrMaker

from ..factories import OrderFactory, TradeFactory
from ..fixtures import trade_dict


@pytest.mark.django_db()
class TestCurrency(unittest.TestCase):
    def test_cost(self):
        """
        test cost
        """
        trade: Trade = TradeFactory()

        assert trade.cost() == Decimal.from_float(1)

    def test_get_or_create_by_api_response_create_new_trade(self):
        """
        get_or_create_by_api_response create new trade
        """
        order: Order = OrderFactory()
        trade: Trade = Trade.get_or_create_by_api_response(
            cctx_trade=trade_dict(), order=order
        )

        assert trade.order == order
        assert trade.trade_id == "12345-67890:09876/54321"
        assert trade.timestamp == datetime(
            year=2017,
            month=8,
            day=17,
            hour=9,
            minute=42,
            second=26,
            microsecond=216000,
            tzinfo=UTC,
        )
        assert trade.taker_or_maker == TakerOrMaker.TAKER
        assert trade.amount == Decimal.from_float(1.5)
        assert trade.fee_currency.short == "ETH"
        assert trade.fee_cost == Decimal.from_float(0.0015)
        assert trade.fee_rate == Decimal.from_float(0.002)

        # get trade from database
        assert trade == Trade.objects.get(pk=trade.pk)

    def test_get_or_create_by_api_response_update_trade(self):
        """
        get_or_create_by_api_response update trade from database
        """
        order: Order = OrderFactory()
        trade_original: Trade = TradeFactory()
        trade_update: Trade = Trade.get_or_create_by_api_response(
            cctx_trade=trade_dict(trade_id=trade_original.trade_id), order=order
        )

        # check if trade_original is the same instance like trade_update
        assert trade_update.pk == trade_original.pk
        assert trade_update.trade_id == trade_original.trade_id

        assert trade_update.order == order
        assert trade_update.timestamp == datetime(
            year=2020,
            month=4,
            day=30,
            hour=23,
            minute=0,
            tzinfo=UTC,
        )
        assert trade_update.taker_or_maker == TakerOrMaker.MAKER
        assert trade_update.amount == Decimal.from_float(1)
        assert trade_update.fee_currency.short == "BNB"
        self.assertAlmostEqual(trade_update.fee_cost, Decimal.from_float(0.01), 8)
        self.assertAlmostEqual(trade_update.fee_rate, Decimal.from_float(0.01), 8)

        # get trade from database
        assert trade_update == Trade.objects.get(pk=trade_update.pk)
