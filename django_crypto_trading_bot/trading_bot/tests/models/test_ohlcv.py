import unittest
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import pytest
import pytz
from _pytest import mark
from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.models import OHLCV, Market
from django_crypto_trading_bot.trading_bot.models.choices import Timeframes
from django_crypto_trading_bot.trading_bot.utils import get_client

from ..factories import MarketFactory


@pytest.mark.django_db()
class TestOHLCV(unittest.TestCase):
    def test_get_OHLCV(self):

        market: Market = MarketFactory()
        timeframe: Timeframes = Timeframes.HOUR_1

        test_candel: List[float] = [
            1504541580000,  # UTC timestamp in milliseconds, integer
            4235.4,  # (O)pen price, float
            4240.6,  # (H)ighest price, float
            4230.0,  # (L)owest price, float
            4230.7,  # (C)losing price, float
            37.72941911,  # (V)olume (in terms of the base currency), float
        ]

        ohlcv: OHLCV = OHLCV.get_OHLCV(
            candle=test_candel, timeframe=timeframe, market=market
        )

        assert ohlcv.market == market
        assert ohlcv.timeframe == timeframe
        assert ohlcv.timestamp == datetime(
            year=2017, month=9, day=4, hour=16, minute=13, tzinfo=pytz.UTC
        )
        assert ohlcv.open_price == Decimal(test_candel[1])
        assert ohlcv.highest_price == Decimal(test_candel[2])
        assert ohlcv.lowest_price == Decimal(test_candel[3])
        assert ohlcv.closing_price == Decimal(test_candel[4])
        assert ohlcv.volume == Decimal(test_candel[5])

    def test_create_OHLCV(self):
        market: Market = MarketFactory()
        timeframe: Timeframes = Timeframes.HOUR_1

        test_candel: List[float] = [
            1504541580000,  # UTC timestamp in milliseconds, integer
            4235.4,  # (O)pen price, float
            4240.6,  # (H)ighest price, float
            4230.0,  # (L)owest price, float
            4230.7,  # (C)losing price, float
            37.72941911,  # (V)olume (in terms of the base currency), float
        ]

        ohlcv: OHLCV = OHLCV.create_OHLCV(
            candle=test_candel, timeframe=timeframe, market=market
        )

        assert isinstance(ohlcv.pk, int)  # check if object was saved to db
        assert ohlcv.market == market
        assert ohlcv.timeframe == timeframe
        assert ohlcv.timestamp == datetime(
            year=2017, month=9, day=4, hour=16, minute=13, tzinfo=pytz.UTC
        )
        assert ohlcv.open_price == Decimal(test_candel[1])
        assert ohlcv.highest_price == Decimal(test_candel[2])
        assert ohlcv.lowest_price == Decimal(test_candel[3])
        assert ohlcv.closing_price == Decimal(test_candel[4])
        assert ohlcv.volume == Decimal(test_candel[5])

    def test_last_candle(self):
        market: Market = MarketFactory()
        timeframe: Timeframes = Timeframes.MINUTE_1

        # test without any candle
        assert OHLCV.last_candle(timeframe=timeframe, market=market) is None

        # test with 1 candles
        OHLCV.create_OHLCV(
            candle=[0, 0, 0, 0, 0, 0], timeframe=timeframe, market=market
        )
        last_candle_1: Optional[OHLCV] = OHLCV.last_candle(
            timeframe=timeframe, market=market
        )
        assert last_candle_1 is not None
        assert last_candle_1.timestamp == datetime(
            year=1970, month=1, day=1, tzinfo=pytz.UTC
        )

        # test with 2 candles
        OHLCV.create_OHLCV(
            candle=[1504541580000, 0, 0, 0, 0, 0], timeframe=timeframe, market=market
        )
        last_candle_2: Optional[OHLCV] = OHLCV.last_candle(
            timeframe=timeframe, market=market
        )
        assert last_candle_2 is not None
        assert last_candle_2.timestamp == datetime(
            year=2017, month=9, day=4, hour=16, minute=13, tzinfo=pytz.UTC
        )

    def test_update_new_candles(self):
        market: Market = MarketFactory()

        # update market with timeframe of 1 month
        OHLCV.update_new_candles(timeframe=Timeframes.MONTH_1, market=MarketFactory())
        assert (
            OHLCV.objects.filter(timeframe=Timeframes.MONTH_1, market=market).count()
            > 20
        )

        # update 550 candles
        exchange: Exchange = get_client(exchange_id=market.exchange)
        exchange_time: int = exchange.milliseconds()
        OHLCV.create_OHLCV(
            candle=[exchange_time - 550 * 1000 * 60, 0, 0, 0, 0, 0],
            timeframe=Timeframes.MINUTE_1,
            market=market,
        )
        OHLCV.update_new_candles(timeframe=Timeframes.MINUTE_1, market=MarketFactory())
        candles_amount: int = OHLCV.objects.filter(
            timeframe=Timeframes.MINUTE_1, market=market
        ).count()
        assert candles_amount >= 550
        assert candles_amount <= 553

    def test_update_new_candles_all_markets(self):
        market: Market = MarketFactory()

        # update market with timeframe of 1 month
        OHLCV.update_new_candles_all_markets(timeframe=Timeframes.MONTH_1)
        # assert (
        #     OHLCV.objects.filter(timeframe=Timeframes.MONTH_1, market=market).count()
        #     > 20
        # )
