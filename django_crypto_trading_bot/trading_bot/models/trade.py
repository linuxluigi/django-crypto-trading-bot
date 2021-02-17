from datetime import datetime
from decimal import Decimal
from typing import Tuple

import pytz
from django.db import models

from .choices import TakerOrMaker
from .currency import Currency


class Trade(models.Model):
    """
    Trade based on https://github.com/ccxt/ccxt/wiki/Manual#trade-structure
    """

    order = models.ForeignKey(
        "trading_bot.Order", related_name="trade_order", on_delete=models.CASCADE
    )
    trade_id = models.CharField(max_length=255, unique=True)
    timestamp = models.DateTimeField()
    taker_or_maker = models.CharField(max_length=8, choices=TakerOrMaker.choices)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    fee_currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    fee_cost = models.DecimalField(max_digits=30, decimal_places=8)
    fee_rate = models.DecimalField(
        max_digits=30, decimal_places=8, blank=True, null=True
    )

    def cost(self):
        return self.amount * self.order.price

    @staticmethod
    def get_or_create_by_api_response(
        cctx_trade: dict, order: "trading_bot.Order"
    ) -> "Trade":
        """
        get or create a trade by a api response dict

        Args:
            cctx_trade (dict): api response dict
            order (Order): trade order

        Returns:
            Trade: get or created trade
        """
        try:
            return Trade.objects.get(trade_id=cctx_trade["id"], order=order)
        except Trade.DoesNotExist:
            trade_currency: Currency
            trade_currency, _ = Currency.objects.get_or_create(
                short=cctx_trade["fee"]["currency"]
            )
            return Trade.objects.create(
                order=order,
                trade_id=cctx_trade["id"],
                timestamp=datetime.fromtimestamp(
                    cctx_trade["timestamp"] / 1000, tz=pytz.timezone("UTC")
                ),
                taker_or_maker=TakerOrMaker(cctx_trade["takerOrMaker"]),
                amount=Decimal(cctx_trade["amount"]),
                fee_currency=trade_currency,
                fee_cost=Decimal(cctx_trade["fee"]["cost"]),
                fee_rate=Decimal(cctx_trade["fee"]["rate"]),
            )
