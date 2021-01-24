from decimal import Decimal

from ccxt.base.exchange import Exchange
from django.db import models

from django_crypto_trading_bot.users.models import User

from ..utils import get_client
from .choices import ExchangesOptions


class Account(models.Model):
    """
    API Account
    for an exchange like binance
    """

    exchange = models.CharField(max_length=250, choices=ExchangesOptions.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=250)
    secret = models.CharField(max_length=250)
    password = models.CharField(max_length=250, blank=True, null=True)
    default_fee_rate = models.DecimalField(
        max_digits=30, decimal_places=4, default=Decimal(0.1)
    )

    def get_account_client(self) -> Exchange:
        return get_client(
            exchange_id=self.exchange, api_key=self.api_key, secret=self.secret
        )

    def __str__(self):
        return "{0}: {1} - {2}".format(self.pk, self.exchange, self.user.get_username())
