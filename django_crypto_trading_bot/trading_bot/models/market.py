from decimal import Decimal, getcontext

from django.db import models

from .choices import ExchangesOptions
from .currency import Currency


class Market(models.Model):
    """
    Market model based on https://github.com/ccxt/ccxt/wiki/Manual#market-structure
    """

    base = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="base")
    quote = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="quote")
    active = models.BooleanField(default=True)
    exchange = models.CharField(max_length=250, choices=ExchangesOptions.choices)
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

        getcontext().prec = 20
        return amount.quantize(Decimal(".1") ** self.precision_amount)

    def __str__(self) -> str:
        return self.symbol
