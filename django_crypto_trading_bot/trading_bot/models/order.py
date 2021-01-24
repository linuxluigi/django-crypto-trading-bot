from decimal import Decimal

from django.db import models

from .choices import OrderSide, OrderStatus, OrderType
from .currency import Currency
from .market import Market


class Order(models.Model):
    """
    Order based on https://github.com/ccxt/ccxt/wiki/Manual#order-structure
    """

    order_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.OPEN
    )
    order_type = models.CharField(max_length=8, choices=OrderType.choices)
    side = models.CharField(max_length=4, choices=OrderSide.choices)
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

    # rising chart
    last_price_tick = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )
    market = models.ForeignKey(
        Market, on_delete=models.PROTECT, blank=True, null=True
    )  # Cryptomarket like TRX/BNB

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

    def __str__(self):
        return "{0}: {1}".format(self.pk, self.order_id)
