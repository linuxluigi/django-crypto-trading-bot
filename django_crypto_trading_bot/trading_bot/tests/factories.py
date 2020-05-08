from datetime import datetime
from decimal import Decimal

import pytz
from config.settings.base import env
from django.utils import timezone
from django_crypto_trading_bot.trading_bot.models import OHLCV, Exchanges, Order
from django_crypto_trading_bot.users.tests.factories import UserFactory
from factory import DjangoModelFactory, SubFactory


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Account"
        django_get_or_create = ["api_key"]

    exchange = Exchanges.BINANCE
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


class EurCurrencyFactory(TrxCurrencyFactory):
    name = "Euro"
    short = "EUR"


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
    exchange = Exchanges.BINANCE
    active = True
    precision_amount = 3
    precision_price = 4
    limits_amount_min = Decimal(0.1)
    limits_amount_max = Decimal(1000)
    limits_price_min = Decimal(0.1)
    limits_price_max = Decimal(1000)


class BnbEurMarketFactory(MarketFactory):
    base = SubFactory(BnbCurrencyFactory)
    quote = SubFactory(EurCurrencyFactory)


class OutOfDataMarketFactory(MarketFactory):
    base = SubFactory(BtcCurrencyFactory)
    quote = SubFactory(UsdtCurrencyFactory)
    active = False
    precision_amount = 10
    precision_price = 10
    limits_amount_min = Decimal(0.1)
    limits_amount_max = Decimal(1000)
    limits_price_min = Decimal(0.1)
    limits_price_max = Decimal(1000)


class BotFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Bot"

    account = SubFactory(AccountFactory)
    market = SubFactory(MarketFactory)
    day_span = 1


class BuyOrderFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Order"
        django_get_or_create = ["order_id"]

    bot = SubFactory(BotFactory)
    order_id = "1"
    timestamp = timezone.now()
    status = Order.Status.CLOSED
    order_type = Order.OrderType.LIMIT
    side = Order.Side.SIDE_BUY
    price = 1
    amount = 100
    filled = 100
    fee_currency = SubFactory(BnbCurrencyFactory)
    fee_cost = 1
    fee_rate = 1


class SellOrderFactory(BuyOrderFactory):
    order_id = "2"
    side = Order.Side.SIDE_SELL


class OHLCVBnbEurFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.OHLCV"
        django_get_or_create = ["market", "timestamp", "timeframe"]

    market = SubFactory(BnbEurMarketFactory)
    timeframe = OHLCV.Timeframes.MINUTE_1
    timestamp = datetime(
        year=2020, month=4, day=30, hour=23, tzinfo=pytz.timezone("UTC")
    )
    open_price = Decimal(0)
    highest_price = Decimal(0)
    lowest_price = Decimal(0)
    closing_price = Decimal(15.7987)
    volume_price = Decimal(0)


class OHLCVTrxBnbFactory(OHLCVBnbEurFactory):
    market = SubFactory(MarketFactory)
    closing_price = Decimal(15.7987)
