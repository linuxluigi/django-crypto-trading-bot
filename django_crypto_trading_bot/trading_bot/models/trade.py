from decimal import Decimal

from django.db import models

from .choices import OrderType
from .currency import Currency
from .order import Order


class Trade(models.Model):
    """
    Trade based on https://github.com/ccxt/ccxt/wiki/Manual#trade-structure
    """

    order = models.ForeignKey(
        Order, related_name="trade_order", on_delete=models.CASCADE
    )
    trade_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    taker_or_maker = models.CharField(max_length=8, choices=OrderType.choices)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def cost(self):
        return self.amount * self.order.price
