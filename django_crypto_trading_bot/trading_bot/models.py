from __future__ import annotations

import logging
from datetime import datetime
from decimal import ROUND_DOWN, Decimal, getcontext
from functools import partial
from multiprocessing.pool import ThreadPool
from time import sleep
from typing import List, Optional

import pytz
from ccxt.base.errors import RequestTimeout
from ccxt.base.exchange import Exchange
from django.db import models
from django.utils import timezone

from django_crypto_trading_bot.users.models import User

from .api.client import get_client
from .exceptions import PriceToHigh, PriceToLow

# Get an instance of a logger
logger = logging.getLogger(__name__)


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
    default_fee_rate = models.DecimalField(
        max_digits=30, decimal_places=4, default=Decimal(0.01)
    )

    def get_account_client(self) -> Exchange:
        return get_client(
            exchange_id=self.exchange, api_key=self.api_key, secret=self.secret
        )

    def __str__(self):
        return "{0}: {1} - {2}".format(self.pk, self.exchange, self.user.get_username())


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

    def get_min_max_price(self, price: Decimal) -> Decimal:
        """
        set the buy & sell min & max prices
        """
        if price < self.limits_price_min:
            price = self.limits_price_min
        if price > self.limits_price_max:
            price = self.limits_price_max
        return price

    def get_min_max_order_amount(self, amount: Decimal) -> Decimal:
        """
        set the buy & sell min & max amount
        """
        if amount < self.limits_amount_min:
            amount = Decimal(0)
        if amount > self.limits_amount_max:
            amount = self.limits_amount_max

        # if self.precision_amount:
        print(self.precision_amount)
        getcontext().prec = 20
        return amount.quantize(Decimal(".1") ** self.precision_amount)
        # return Decimal(int(amount))

    def __str__(self) -> str:
        return self.symbol


class OrderErrorLog(models.Model):
    class ErrorTypes(models.TextChoices):
        Insufficient_Funds = "Insufficient Funds"
        InvalidOrder = "Invalid Order"

    order = models.ForeignKey(
        "trading_bot.Order", related_name="error_log", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    error_type = models.CharField(max_length=50, choices=ErrorTypes.choices)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return "{0}: {1}".format(self.created, self.error_type)


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
        NOT_MIN_NOTIONAL = "not min notional"

    # ORDER_TYPE_CHOICE
    class OrderType(models.TextChoices):
        MARKET = "market"
        LIMIT = "limit"

    # SIDE_CHOICE
    class Side(models.TextChoices):
        SIDE_BUY = "buy"
        SIDE_SELL = "sell"

    bot = models.ForeignKey("trading_bot.Bot", on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    order_type = models.CharField(max_length=8, choices=OrderType.choices)
    side = models.CharField(max_length=4, choices=Side.choices)
    price = models.DecimalField(max_digits=30, decimal_places=8)  # quote currency
    amount = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # ordered amount of base currency
    filled = models.DecimalField(
        max_digits=30, decimal_places=8, default=0
    )  # filled amount of base currency
    next_order = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True
    )
    fee_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, blank=True, null=True
    )
    fee_cost = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

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
        if self.fee_cost and self.bot.market.base == self.fee_currency:
            return self.filled - self.fee_cost

        return self.filled

    def quote_amount(self) -> Decimal:
        """
        Get quote amount minus cost
        Returns:
            Decimal -- [description]
        """
        # todo logic error?
        if self.fee_cost and self.bot.market.quote == self.fee_currency:
            return self.cost() - self.fee_cost

        return self.cost()

    def get_retrade_amount(self, price: Decimal) -> Decimal:
        """
        get retrade amount

        Returns:
            Decimal -- retrade amount
        """
        if price < self.bot.market.limits_price_min:
            raise PriceToLow()
        if price > self.bot.market.limits_price_max:
            raise PriceToHigh()

        getcontext().rounding = ROUND_DOWN

        amount: Decimal = Decimal(self.amount)

        fee_rate: Decimal
        if self.fee_rate:
            fee_rate = self.fee_rate
        else:
            fee_rate = self.bot.account.default_fee_rate

        fee_cost: Decimal = amount * fee_rate / Decimal(100)

        amount -= fee_cost

        if self.side == Order.Side.SIDE_SELL:
            quote_amount: Decimal = amount * self.price
            amount = quote_amount / price

        amount -= amount % self.bot.market.limits_amount_min

        return self.bot.market.get_min_max_order_amount(amount=amount)

    @property
    def errors(self) -> int:
        return OrderErrorLog.objects.filter(order=self).count()

    def __str__(self):
        return "{0}: {1}".format(self.pk, self.order_id)


class Bot(models.Model):
    """
    Trading Bot
    """

    account = models.ForeignKey(Account, on_delete=models.CASCADE)  # API Account
    market = models.ForeignKey(
        Market, on_delete=models.PROTECT
    )  # Cryptomarket like TRX/BNB
    created = models.DateTimeField(auto_now_add=True)
    timeframe = models.CharField(
        max_length=10, choices=Timeframes.choices, default=Timeframes.MONTH_1
    )
    active = models.BooleanField(default=True)

    @property
    def start_amount(self) -> Optional[Decimal]:
        orders: models.Manager[Order] = Order.objects.filter(bot=self).order_by(
            "timestamp"
        )[:1]
        if len(orders):
            return orders[0].amount
        return None

    @property
    def current_amount(self) -> Optional[Decimal]:
        orders: models.Manager[Order] = Order.objects.filter(
            bot=self, status=Order.Status.CLOSED
        ).order_by("-timestamp")[:1]
        if len(orders):
            return orders[0].amount
        return None

    @property
    def roi(self) -> Optional[Decimal]:
        start_amount: Optional[Decimal] = self.start_amount
        if not start_amount:
            return None

        current_amount: Optional[Decimal] = self.current_amount
        if not current_amount:
            return None

        getcontext().prec = 2
        win: Decimal = current_amount - start_amount
        return win / current_amount * Decimal(100)

    @property
    def orders_count(self) -> int:
        return Order.objects.filter(bot=self).count()

    def __str__(self):
        return "{0}: {1} - {2}".format(
            self.pk, self.account.user.get_username(), self.market
        )


class Saving(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=30, decimal_places=8
    )  # ordered amount of base currency
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)


class Trade(models.Model):
    """
    Trade based on https://github.com/ccxt/ccxt/wiki/Manual#trade-structure
    """

    order = models.ForeignKey(
        Order, related_name="trade_order", on_delete=models.CASCADE
    )
    # re_order = models.ForeignKey(
    #     Order, related_name="re_order", on_delete=models.CASCADE, blank=True, null=True
    # )
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

    def get_retrade_amount(self) -> Decimal:
        """
        get retrade amount

        Returns:
            Decimal -- retrade amount
        """
        getcontext().prec = self.order.bot.market.precision_amount
        getcontext().rounding = ROUND_DOWN
        amount: Decimal = self.amount - self.fee_cost
        amount -= amount % self.order.bot.market.limits_amount_min
        return self.order.bot.market.get_min_max_order_amount(amount=amount)

    def get_retrade_price(self, price: Decimal) -> Decimal:
        """
        get retrade amount

        Arguments:
            price {Decimal} -- price

        Returns:
            Decimal -- retrade amount
        """
        getcontext().prec = self.order.bot.market.precision_price
        price -= price % self.order.bot.market.limits_price_min

        return self.order.bot.market.get_min_max_price(price=price)


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
    def get_OHLCV(candle: List[float], timeframe: str, market: Market) -> OHLCV:
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
    ) -> OHLCV:
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
    def update_new_candles(market: Market, timeframe: Timeframes):
        """Update all candles for a single market of a timeframe

        Arguments:
            market {Market} -- market from candle
            timeframe {Timeframes} -- timeframe from candle
        """
        exchange: Exchange = get_client(exchange_id=market.exchange)

        last_candle: Optional[OHLCV] = OHLCV.last_candle(
            timeframe=timeframe, market=market
        )
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
            except RequestTimeout as e:
                logger.warning(
                    "Connetion error from {} ... wait 120s for next try".format(
                        market.exchange
                    )
                )
                sleep(120)
                continue

            for candle in candles:
                ohlcvs.append(
                    OHLCV.get_OHLCV(candle=candle, timeframe=timeframe, market=market)
                )

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
