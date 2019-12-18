from factory import DjangoModelFactory, Faker, post_generation, SubFactory
from typing import Any, Sequence
from django_crypto_trading_bot.users.models import User
from django_crypto_trading_bot.users.tests.factories import UserFactory
from config.settings.base import env
import pytest


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Account"
        django_get_or_create = ["api_key"]

    exchange = "binance"
    user = SubFactory(UserFactory)
    api_key = env("BINANCE_SANDBOX_API_KEY")
    secret = env("BINANCE_SANDBOX_SECRET_KEY")


class TrxCurrencyFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Currency"
        django_get_or_create = ["short"]

    name = "TRON"
    short = "TRX"


class BnbCurrencyFactory(TrxCurrencyFactory):
    name = "Binance Coin"
    short = "BNB"


class BtcCurrencyFactory(TrxCurrencyFactory):
    name = "Bitcoin"
    short = "BTC"


class UsdtCurrencyFactory(TrxCurrencyFactory):
    name = "Tether"
    short = "USDT"


class MarketFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Market"
        django_get_or_create = ["base", "quote"]

    base = SubFactory(TrxCurrencyFactory)
    quote = SubFactory(BnbCurrencyFactory)
    active = True
    precision_amount = 0
    precision_price = 6


class OutOfDataMarketFactory(MarketFactory):
    base = SubFactory(BtcCurrencyFactory)
    quote = SubFactory(UsdtCurrencyFactory)
    active = False
    precision_amount = 10
    precision_price = 10


class BotFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Bot"
        django_get_or_create = ["api_key"]

    account = SubFactory(AccountFactory)
    market = SubFactory(MarketFactory)
    day_span = 1
