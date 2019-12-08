from django.db import models
import ccxt
from django_crypto_trading_bot.users.models import User
from ccxt.base.exchange import Exchange


class Account(models.Model):
    EXCHANGES = (
        ("Kucoin", "kucoin"),
        ("Binance", "binance"),
    )

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
