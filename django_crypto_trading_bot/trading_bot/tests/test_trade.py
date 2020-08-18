import unittest
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.utils import timezone

from django_crypto_trading_bot.trading_bot.models import (
    Bot,
    OHLCV,
    Order,
    Saving,
    Timeframes,
)
from django_crypto_trading_bot.trading_bot.tests.factories import (
    BnbEurMarketFactory,
    BtcBnbMarketFactory,
    BuyOrderFactory,
    EndOrderFactory,
    EthBnbMarketFactory,
    MarketFactory,
    OpenBuyOrderFactory,
    SellOrderFactory,
    RisingChartOrderFactory,
    RisingChartBotFactory,
)
from django_crypto_trading_bot.trading_bot.trade import run_rising_chart, run_wave_rider


@pytest.mark.django_db()
class TestWaveRider(unittest.TestCase):
    def test_no_update(self):
        open_order: Order = OpenBuyOrderFactory()
        end_order: Order = EndOrderFactory()

        run_wave_rider(test=True)

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
            timeframe=Timeframes.MONTH_1,
            timestamp=timezone.now(),
            open_price=Decimal(8.3),
            highest_price=Decimal(9.4),
            lowest_price=Decimal(7.5),
            closing_price=Decimal(8),
            volume=Decimal(100),
        )

        run_wave_rider(candle=candle, test=True)

        buy_order_reload: Order = Order.objects.get(pk=buy_order.pk)
        sell_order_reload: Order = Order.objects.get(pk=sell_order.pk)

        assert buy_order_reload.next_order is not None
        assert sell_order_reload.next_order is not None

        Saving.objects.get(order=sell_order)

        assert Saving.objects.all().count() == 2


@pytest.mark.django_db()
class TestRisingChart(unittest.TestCase):
    def set_tickers_cache(self, exchange: str):
        MarketFactory().save()
        BnbEurMarketFactory().save()
        EthBnbMarketFactory().save()
        BtcBnbMarketFactory().save()

        tickers: dict = {
            "BNB/EUR": {
                "symbol": "BNB/EUR",
                "percentage": 2.0,
                "last": 1.0,
                "bid": 1.0,
                "ask": 1.0,
            },
            "TRX/BNB": {
                "symbol": "TRX/BNB",
                "percentage": 6.0,
                "last": 1.0,
                "bid": 1.0,
                "ask": 1.0,
            },
            "ETH/BNB": {
                "symbol": "ETH/BNB",
                "percentage": 10.0,
                "last": 1.0,
                "bid": 1.0,
                "ask": 1.0,
            },
            "BTC/BNB": {
                "symbol": "BTC/BNB",
                "percentage": -2.0,
                "last": 1.0,
                "bid": 1.0,
                "ask": 1.0,
            },
        }

        cache.set("tickers-{}".format(exchange), tickers, 60)

    def test_order_stop_loss(self):
        order: Order = RisingChartOrderFactory()
        order.last_price_tick = Decimal(10)
        order.save()

        self.set_tickers_cache(order.bot.account.exchange)

        run_rising_chart(test=True)

        order_buy: Order = Order.objects.get(pk=order.pk)

        assert order_buy.next_order is not None

    def test_order_update_order(self):
        order: Order = RisingChartOrderFactory()
        order.last_price_tick = Decimal(0.5)
        order.save()

        self.set_tickers_cache(order.bot.account.exchange)

        run_rising_chart(test=True)

        order_buy: Order = Order.objects.get(pk=order.pk)

        assert order_buy.last_price_tick is not None
        assert "{:0.1f}".format(order_buy.last_price_tick) == "1.0"
        assert order_buy.next_order is None

    def test_init_buy_order(self):
        bot: Bot = RisingChartBotFactory()
        bot.save()

        self.set_tickers_cache(bot.account.exchange)

        run_rising_chart(test=True)

        order_buy: Order = Order.objects.get(bot=bot)

        assert order_buy.next_order is None
        assert order_buy.market is not None
        assert order_buy.market.symbol.upper() == "ETH/BNB"
