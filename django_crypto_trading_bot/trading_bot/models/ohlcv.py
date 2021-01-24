# Get an instance of a logger
import logging
from datetime import datetime
from decimal import Decimal
from functools import partial
from multiprocessing.pool import ThreadPool
from time import sleep
from typing import List, Optional, Union

import pytz
from ccxt.base.errors import RequestTimeout
from ccxt.base.exchange import Exchange
from django.db import models

from ..utils import get_client
from .choices import Timeframes
from .market import Market

logger = logging.getLogger(__name__)


class OHLCV(models.Model):
    """
    OHLCV candles https://github.com/ccxt/ccxt/wiki/Manual#ohlcv-structure
    """

    market = models.ForeignKey(Market, on_delete=models.PROTECT)
    timeframe = models.CharField(max_length=10, choices=Timeframes.choices)
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=30, decimal_places=8)
    highest_price = models.DecimalField(max_digits=30, decimal_places=8)
    lowest_price = models.DecimalField(max_digits=30, decimal_places=8)
    closing_price = models.DecimalField(max_digits=30, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)

    @staticmethod
    def get_OHLCV(
        candle: List[float], timeframe: str, market: Market
    ) -> Optional["OHLCV"]:
        """Get a OHLCV candle from a OHLCV request
        Arguments:
            candle {List[float]} -- candle list
            timeframe {Timeframes} -- timeframe from candle
            market {Market} -- market from candle
        Returns:
            OHLCV -- unsaved OHLCV candle
        """
        return OHLCV(
            market=market,
            timeframe=timeframe,
            timestamp=datetime.fromtimestamp(candle[0] / 1000, tz=pytz.timezone("UTC")),
            open_price=Decimal(candle[1]),
            highest_price=Decimal(candle[2]),
            lowest_price=Decimal(candle[3]),
            closing_price=Decimal(candle[4]),
            volume=Decimal(candle[5]),
        )

    @staticmethod
    def create_OHLCV(
        candle: List[float], timeframe: Timeframes, market: Market
    ) -> "OHLCV":
        """Get a saved OHLCV candle from a OHLCV request
        Arguments:
            candle {List[float]} -- candle list
            timeframe {Timeframes} -- timeframe from candle
            market {Market} -- market from candle
        Returns:
            OHLCV -- saved OHLCV candle
        """
        ohlcv: OHLCV = OHLCV.get_OHLCV(
            candle=candle, timeframe=timeframe, market=market
        )
        ohlcv.save()
        return ohlcv

    @staticmethod
    def last_candle(timeframe: Timeframes, market: Market) -> "OHLCV":
        """Get last candle by timestamp of market & timeframe
        Arguments:
            timeframe {Timeframes} -- timeframe from candle
            market {Market} -- market from candle
        Returns:
            Optional[OHLCV] -- last candle by timestamp of market & timeframe
        """
        return (
            OHLCV.objects.filter(timeframe=timeframe, market=market)
            .order_by("timestamp")
            .last()
        )

    @staticmethod
    def update_new_candles(market: Market, timeframe: Timeframes):
        """Update all candles for a single market of a timeframe
        Arguments:
            market {Market} -- market from candle
            timeframe {Timeframes} -- timeframe from candle
        """
        exchange: Exchange = get_client(exchange_id=market.exchange)

        last_candle: List[OHLCV] = OHLCV.last_candle(timeframe=timeframe, market=market)
        last_candle_time: int = 0

        if last_candle:
            last_candle_time = int(last_candle.timestamp.timestamp()) * 1000

        ohlcvs: List[OHLCV] = list()

        while True:
            try:
                candles: List[List[float]] = exchange.fetch_ohlcv(
                    symbol=market.symbol,
                    timeframe=timeframe,
                    since=last_candle_time + 1,
                )
            except RequestTimeout:
                logger.warning(
                    "Connetion error from {} ... wait 120s for next try".format(
                        market.exchange
                    )
                )
                sleep(120)
                continue

            for candle in candles:
                ohlcv: Optional[OHLCV] = OHLCV.get_OHLCV(
                    candle=candle, timeframe=timeframe, market=market
                )
                if ohlcv:
                    ohlcvs.append(ohlcv)

            if len(ohlcvs) >= 10000:
                OHLCV.objects.bulk_create(ohlcvs)
                ohlcvs.clear()

            # no new candles
            if len(candles) == 0:
                break

            last_candle_time = int(candles[-1][0])

        OHLCV.objects.bulk_create(ohlcvs)
        ohlcvs.clear()

        logger.info(
            "Update market {} for timeframe {}.".format(market.symbol, timeframe)
        )

    @staticmethod
    def update_new_candles_all_markets(timeframe: Timeframes):
        """Update all candles for all markets of a timeframe
        Arguments:
            timeframe {Timeframes} -- timeframe from candle
        """

        markets: List[Market] = list()
        for market in Market.objects.filter(active=True):
            markets.append(market)

        # Make the Pool of workers
        pool = ThreadPool(8)

        pool.map(partial(OHLCV.update_new_candles, timeframe=timeframe), markets)

        # Close the pool and wait for the work to finish
        pool.close()
        pool.join()
