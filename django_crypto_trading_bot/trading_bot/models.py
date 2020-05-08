from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import pytz
from ccxt.base.exchange import Exchange
from django.db import models
from django.utils import timezone

from django_crypto_trading_bot.users.models import User

from .api.client import get_client


class Exchanges(models.TextChoices):
    BINANCE = "binance"


class Account(models.Model):
    """
    API Account
    for an exchange like binance
    """

    exchange = models.CharField(max_length=250, choices=Exchanges.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=250)
    secret = models.CharField(max_length=250)
    password = models.CharField(max_length=250, blank=True, null=True)

    def get_account_client(self) -> Exchange:
        return get_client(
            exchange_id=self.exchange, api_key=self.api_key, secret=self.secret
        )

    def __str__(self):
        return "{1}: {1}".format(self.exchange, self.user.get_username())


class Currency(models.Model):
    """
    Cryptocurrency
    """

    name = models.CharField(max_length=50, blank=True, null=True)
    short = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return "{0}: {1}".format(self.pk, self.short)


class Market(models.Model):
    """
    Market model based on https://github.com/ccxt/ccxt/wiki/Manual#market-structure
    """

    base = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="base")
    quote = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="quote")
    active = models.BooleanField(default=True)
    exchange = models.CharField(max_length=250, choices=Exchanges.choices)
    precision_amount = models.IntegerField()
    precision_price = models.IntegerField()
    limits_amount_min = models.DecimalField(max_digits=30, decimal_places=8)
    limits_amount_max = models.DecimalField(max_digits=30, decimal_places=8)
    limits_price_min = models.DecimalField(max_digits=30, decimal_places=8)
    limits_price_max = models.DecimalField(max_digits=30, decimal_places=8)

    @property
    def symbol(self):
        return "{}/{}".format(self.base.short.upper(), self.quote.short.upper())

    @property
    def market_id(self):
        return "{}{}".format(self.base.short.lower(), self.quote.short.lower())

    @property
    def baseId(self):
        return self.base.short.lower()

    @property
    def quoteId(self):
        return self.quote.short.lower()

    def __str__(self) -> str:
        return self.symbol


class Bot(models.Model):
    """
    Trading Bot
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE)  # API Account
    market = models.ForeignKey(
        Market, on_delete=models.PROTECT
    )  # Cryptomarket like TRX/BNB
    created = models.DateTimeField(auto_now_add=True)
    day_span = models.IntegerField(
        default=30
    )  # how many days will be analysed for new trading order
    min_profit = models.DecimalField(
        max_digits=30, decimal_places=2, default=0.1
    )  # min profit for each trade in percent


class Order(models.Model):
    """
    Order based on https://github.com/ccxt/ccxt/wiki/Manual#order-structure
    """

    # STATUS_CHOICE
    class Status(models.TextChoices):
        OPEN = "open"
        CLOSED = "closed"
        CANCELED = "canceled"
        EXPIRED = "expired"
        REJECTED = "rejected"
        REORDERD = "reorderd"

    # ORDER_TYPE_CHOICE
    class OrderType(models.TextChoices):
        MARKET = "market"
        LIMIT = "limit"

    # SIDE_CHOICE
    class Side(models.TextChoices):
        SIDE_BUY = "buy"
        SIDE_SELL = "sell"

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    exchange = models.CharField(max_length=250, choices=Exchanges.choices)
    order_type = models.CharField(max_length=8, choices=OrderType.choices)
    side = models.CharField(max_length=4, choices=Side.choices)
    price = models.DecimalField(max_digits=30, decimal_places=8)  # quote currency
    amount = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # ordered amount of base currency
    filled = models.DecimalField(
        max_digits=30, decimal_places=8, default=0
    )  # filled amount of base currency
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )
    # reorder = models.ForeignKey("self", blank=True, null=True, on_delete=models.CASCADE)

    def remaining(self) -> Decimal:
        """
        remaining amount to fill
        """
        return self.amount - self.filled

    def cost(self) -> Decimal:
        """
        'filled' * 'price' (filling price used where available)
        """
        return self.filled * self.price

    def base_amount(self) -> Decimal:
        """
        Get base amount minus cost

        Returns:
            Decimal -- [description]
        """

        if self.bot.market.base == self.fee_currency:
            return self.filled - self.fee_cost

        return self.filled

    def quote_amount(self) -> Decimal:
        """
        Get quote amount minus cost

        Returns:
            Decimal -- [description]
        """
        if self.bot.market.quote == self.fee_currency:
            return self.cost() - self.fee_cost

        return self.cost


class Trade(models.Model):
    """
    Trade based on https://github.com/ccxt/ccxt/wiki/Manual#trade-structure
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    trade_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    taker_or_maker = models.CharField(max_length=8, choices=Order.OrderType.choices)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def cost(self):
        return self.amount * self.order.price


class OHLCV(models.Model):
    """
    OHLCV candles https://github.com/ccxt/ccxt/wiki/Manual#ohlcv-structure
    """

    class Timeframes(models.TextChoices):
        MINUTE_1 = "1m"
        MINUTE_3 = "3m"
        MINUTE_5 = "5m"
        MINUTE_15 = "15m"
        MINUTE_30 = "30m"
        HOUR_1 = "1h"
        HOUR_2 = "2h"
        HOUR_4 = "4h"
        HOUR_6 = "6h"
        HOUR_8 = "8h"
        HOUR_12 = "12h"
        DAY_1 = "1d"
        DAY_3 = "3d"
        WEEK_1 = "1w"
        MONTH_1 = "1M"

    market = models.ForeignKey(Market, on_delete=models.PROTECT)
    timeframe = models.CharField(max_length=10, choices=Timeframes.choices)
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=30, decimal_places=8)
    highest_price = models.DecimalField(max_digits=30, decimal_places=8)
    lowest_price = models.DecimalField(max_digits=30, decimal_places=8)
    closing_price = models.DecimalField(max_digits=30, decimal_places=8)
    volume_price = models.DecimalField(max_digits=30, decimal_places=8)

    @staticmethod
    def get_OHLCV(candle: List[int], timeframe: Timeframes, market: Market) -> OHLCV:
        """Get a OHLCV candle from a OHLCV request

        Arguments:
            candle {List[int]} -- candle list
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
            volume_price=Decimal(candle[5]),
        )

    @staticmethod
    def create_OHLCV(candle: List[int], timeframe: Timeframes, market: Market) -> OHLCV:
        """Get a saved OHLCV candle from a OHLCV request

        Arguments:
            candle {List[int]} -- candle list
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
    def last_candle(timeframe: Timeframes, market: Market) -> Optional[OHLCV]:
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
    def update_new_candles(timeframe: Timeframes, market: Market):
        """Update all candles for a single market of a timeframe

        Arguments:
            timeframe {Timeframes} -- timeframe from candle
            market {Market} -- market from candle
        """
        exchange: Exchange = get_client(exchange_id=market.exchange)

        last_candle: Optional[OHLCV] = OHLCV.last_candle(
            timeframe=timeframe, market=market
        )
        last_candle_time: int = 0

        if last_candle:
            last_candle_time = int(last_candle.timestamp.timestamp()) * 1000

        while True:
            candles: List[dict] = exchange.fetch_ohlcv(
                symbol=market.symbol, timeframe=timeframe, since=last_candle_time + 1
            )

            for candle in candles:
                OHLCV.create_OHLCV(candle=candle, timeframe=timeframe, market=market)

            # no new candles
            if len(candles) == 0:
                break

            last_candle_time = candles[-1][0]

    @staticmethod
    def update_new_candles_all_markets(timeframe: Timeframes):
        """Update all candles for all markets of a timeframe

        Arguments:
            timeframe {Timeframes} -- timeframe from candle
        """
        for market in Market.objects.filter(active=True):
            print("Update market {} for timeframe {}.".format(market.symbol, timeframe))
            OHLCV.update_new_candles(timeframe=timeframe, market=market)


class Simulation(models.Model):
    """
    Simulation results
    """

    market = models.ForeignKey(
        Market, on_delete=models.PROTECT
    )  # Cryptomarket like TRX/BNB
    created = models.DateTimeField(auto_now_add=True)
    day_span = models.IntegerField(
        default=30
    )  # how many days will be analysed for new trading order
    min_profit = models.DecimalField(
        max_digits=30, decimal_places=2, default=0.1
    )  # min profit for each trade in percent
    history_days = models.IntegerField(default=365)  # how many days will be simulated
    start_simulation = models.DateTimeField()  # time begin of the first simulation
    end_simulation = models.DateTimeField()  # time end of the last simulation
    simulation_amount = models.IntegerField()  # how many simulation was used
    start_amount_eur = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # start amount in euro for each simulation
    end_amount_eur_average = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # average end amount of all simulations
    roi = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # return of investment average
