from django.db import models
import ccxt
from django_crypto_trading_bot.users.models import User
from ccxt.base.exchange import Exchange


class Account(models.Model):
    EXCHANGES = (("Kucoin", "kucoin"), ("Binance", "binance"))

    exchange = models.CharField(max_length=250, choices=EXCHANGES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=250)
    secret = models.CharField(max_length=250)
    password = models.CharField(max_length=250, blank=True, null=True)
    sandbox = models.BooleanField(default=False)

    def get_client(self) -> Exchange:
        exchange_id = self.exchange
        exchange_class = getattr(ccxt, exchange_id)
        exchange: Exchange = exchange_class(
            {
                "apiKey": self.api_key,
                "secret": self.secret,
                "password": self.password,
                "timeout": 30000,
                "enableRateLimit": True,
            }
        )

        # set sandbox mode
        exchange.set_sandbox_mode(self.sandbox)

        return exchange

    def __str__(self):
        return "{}: {}".format(self.pk, self.user.get_username())


class Currency(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    short = models.CharField(max_length=50, unique=True)


class Market(models.Model):
    first_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="first_currency"
    )
    secound_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="secound_currency"
    )

    def symbol(self):
        return "{}/{}".format(self.first_currency.short, self.secound_currency.short)

    def __str__(self) -> str:
        return self.symbol()


class Bot(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
    day_span = models.IntegerField(default=30)
    min_profit = models.DecimalField(max_digits=30, decimal_places=2, default=0.1)


class Order(models.Model):
    status_choice = (("open", "open"), ("closed", "closed"), ("canceled", "canceled"))
    order_type_choice = (("market", "market"), ("limit", "limit"))
    side_choice = (("buy", "buy"), ("sell", "sell"))

    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=10, choices=status_choice, default="open")
    order_type = models.CharField(max_length=8, choices=order_type_choice)
    side = models.CharField(max_length=4, choices=side_choice)
    price = models.DecimalField(max_digits=30, decimal_places=8)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    filled = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def remaining(self) -> str:
        return self.amount - self.filled

    def cost(self) -> str:
        return self.filled * self.price


class Trade(models.Model):
    taker_or_maker_choice = (("market", "market"), ("limit", "limit"))

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    trade_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    taker_or_maker = models.CharField(max_length=8, choices=taker_or_maker_choice)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def cost(self):
        return self.amount * self.order.price
