from datetime import datetime
from decimal import Decimal
from typing import Optional

import pytz
from django.db import models
from django.db.models.manager import BaseManager

from django_crypto_trading_bot.trading_bot.models.trade import Trade

from . import Account, Currency, Market
from .choices import ExchangesOptions, OrderSide, OrderStatus, OrderType


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

    def fee_currency(self) -> Currency:
        pass

    def fee_cost(self) -> Decimal:
        pass

    def fee_rate(self) -> Decimal:
        pass

    @staticmethod
    def get_or_create_by_api_response(cctx_order: dict, account: Account) -> "Order":
        """
        get or create a order by a api response dict

        Args:
            cctx_order (dict): api response dict
            account (Account): exchange account for the order

        Returns:
            Order: new created or updated order
        """
        order: Order

        try:
            order = Order.objects.get(order_id=cctx_order["id"], account=account)
            order.status = cctx_order["status"]
            order.filled = Decimal(cctx_order["filled"])
            order.save()
        except Order.DoesNotExist:
            order = Order.objects.create(
                account=account,
                status=cctx_order["status"],
                order_id=cctx_order["id"],
                order_type=OrderType(cctx_order["type"]),
                side=OrderSide(cctx_order["side"]),
                timestamp=datetime.fromtimestamp(
                    cctx_order["timestamp"] / 1000, tz=pytz.timezone("UTC")
                ),
                price=Decimal(cctx_order["price"]),
                amount=Decimal(cctx_order["amount"]),
                filled=Decimal(cctx_order["filled"]),
                market=Market.get_market(
                    symbol=cctx_order["symbol"],
                    exchange=ExchangesOptions(account.exchange),
                ),
            )

        trade_dict: dict
        for trade_dict in cctx_order["trades"]:
            Trade.get_or_create_by_api_response(cctx_trade=trade_dict, order=order)

        return order

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
