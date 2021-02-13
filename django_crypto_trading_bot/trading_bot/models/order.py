from decimal import Decimal
from typing import Optional

from django.db import models
from django.db.models.manager import BaseManager

from . import Account, Currency, Market
from .choices import OrderSide, OrderStatus, OrderType


class Order(models.Model):
    """
    Order based on https://github.com/ccxt/ccxt/wiki/Manual#order-structure
    """

    account = models.ForeignKey(Account, on_delete=models.PROTECT)  # exchange account
    market = models.ForeignKey(
        Market, on_delete=models.PROTECT
    )  # Cryptomarket like TRX/BNB
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

    @staticmethod
    def last_order(
        account: Account, market: Optional[Market] = None
    ) -> Optional["Order"]:
        """
        Get last order for account

        Arguments:
            account {Account} -- exchange account
            market {Optional[Market]} -- last order from a specific market. Default is None

        Returns:
            Optional[Order] -- last candle by timestamp of market & timeframe
        """
        orders: BaseManager
        if market:
            orders = Order.objects.filter(market=market, account=account).order_by(
                "-timestamp"
            )[:1]
        else:
            orders = Order.objects.filter(account=account).order_by("-timestamp")[:1]

        if len(orders) == 1:
            return orders[0]
        return None

    def __str__(self):
        return "{0}: {1}".format(self.pk, self.order_id)
