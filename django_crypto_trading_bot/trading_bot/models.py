from __future__ import annotations

from decimal import Decimal

from ccxt.base.exchange import Exchange
from django.db import models

from django_crypto_trading_bot.users.models import User

from .api.client import get_client


class Account(models.Model):
    """
    API Account
    for an exchange like binance
    """

    # Exchnages
    EXCHANGE_BINANCE = "Binance"
    EXCHANGES_CHOICE = [(EXCHANGE_BINANCE, EXCHANGE_BINANCE)]

    exchange = models.CharField(max_length=250, choices=EXCHANGES_CHOICE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=250)
    secret = models.CharField(max_length=250)
    password = models.CharField(max_length=250, blank=True, null=True)

    def get_account_client(self) -> Exchange:
        return get_client(
            exchange_id=self.exchange, api_key=self.api_key, secret=self.secret
        )

    def __str__(self):
        return "{}: {}".format(self.pk, self.user.get_username())


class Currency(models.Model):
    """
    Cryptocurrency
    """

    name = models.CharField(max_length=50, blank=True, null=True)
    short = models.CharField(max_length=50, unique=True)


class Market(models.Model):
    """
    Market model based on https://github.com/ccxt/ccxt/wiki/Manual#market-structure
    """

    base = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="base")
    quote = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="quote")
    active = models.BooleanField(default=True)
    exchange = models.CharField(max_length=250, choices=Account.EXCHANGES_CHOICE)
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
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"
    REORDERD = "reorderd"

    STATUS_CHOICE = [
        (OPEN, OPEN),
        (CLOSED, CLOSED),
        (CANCELED, CANCELED),
        (EXPIRED, EXPIRED),
        (REJECTED, REJECTED),
        (REORDERD, REORDERD),
    ]

    # ORDER_TYPE_CHOICE
    MARKET = "market"
    LIMIT = "limit"
    ORDER_TYPE_CHOICE = [
        (MARKET, MARKET),
        (LIMIT, LIMIT),
    ]

    # SIDE_CHOICE
    SIDE_BUY = "buy"
    SIDE_SELL = "sell"
    SIDE_CHOICE = [
        (SIDE_BUY, SIDE_BUY),
        (SIDE_SELL, SIDE_SELL),
    ]

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default="open")
    order_type = models.CharField(max_length=8, choices=ORDER_TYPE_CHOICE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICE)
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
    reorder = models.ForeignKey("self", blank=True, null=True, on_delete=models.CASCADE)

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
    taker_or_maker = models.CharField(max_length=8, choices=Order.ORDER_TYPE_CHOICE)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def cost(self):
        return self.amount * self.order.price
