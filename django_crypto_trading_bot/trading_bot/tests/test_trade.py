import unittest
from decimal import Decimal

import pytest
from django.utils import timezone

from django_crypto_trading_bot.trading_bot.models import (
    OHLCV,
    Order,
    OrderErrorLog,
    Saving,
)
from django_crypto_trading_bot.trading_bot.tests.factories import (
    BuyOrderFactory,
    EndOrderFactory,
    OpenBuyOrderFactory,
    SellOrderFactory,
)
from django_crypto_trading_bot.trading_bot.trade import run_trade


@pytest.mark.django_db()
class Trade(unittest.TestCase):

    def test_no_update(self):
        open_order: Order = OpenBuyOrderFactory()
        end_order: Order = EndOrderFactory()

        run_trade(test=True)

        open_order_update: Order = Order.objects.get(pk=open_order.pk)
        end_order_update: Order = Order.objects.get(pk=end_order.pk)

        assert open_order_update.status == open_order.status
        assert open_order_update.next_order == open_order.next_order

        assert end_order_update.status == end_order.status
        assert end_order_update.next_order == end_order.next_order

    def test_normal_update(self):
        buy_order: Order = BuyOrderFactory()
        sell_order: Order = SellOrderFactory()

        candle: OHLCV = OHLCV(
            market=buy_order.bot.market,
            timeframe=buy_order.bot.timeframe,
            timestamp=timezone.now(),
            open_price=Decimal(8.3),
            highest_price=Decimal(9.4),
            lowest_price=Decimal(7.5),
            closing_price=Decimal(8),
            volume=Decimal(100),
        )

        run_trade(candle=candle, test=True)

        buy_order_reload: Order = Order.objects.get(pk=buy_order.pk)
        sell_order_reload: Order = Order.objects.get(pk=sell_order.pk)

        assert buy_order_reload.next_order != None
        assert sell_order_reload.next_order != None

        sell_saving: Saving = Saving.objects.get(order=sell_order)

        assert Saving.objects.all().count() == 1
