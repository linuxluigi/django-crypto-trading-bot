import pytest
from ccxt import Exchange
from decimal import Decimal

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
    get_or_create_market,
)
from django_crypto_trading_bot.trading_bot.api.order import create_order
from django_crypto_trading_bot.trading_bot.models import Order, Market, Bot
from django_crypto_trading_bot.trading_bot.tests.factories import (
    AccountFactory,
    BotFactory,
)
from typing import List


@pytest.mark.django_db()
def test_create_buy_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    bot = BotFactory()

    order: Order = create_order(
        amount=Decimal(1), price=Decimal(0.01), side="buy", bot=bot, isTestOrder=True,
    )
    order2: Order = create_order(
        amount=Decimal(1), price=Decimal(0.01), side="buy", bot=bot, isTestOrder=True,
    )

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "buy"
    assert len(Order.objects.all()) == 2


@pytest.mark.django_db()
def test_create_sell_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    bot = BotFactory()
    order: Order = create_order(
        amount=Decimal(1), price=Decimal(0.01), side="sell", bot=bot, isTestOrder=True,
    )
    order2: Order = create_order(
        amount=Decimal(1), price=Decimal(0.01), side="sell", bot=bot, isTestOrder=True,
    )

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "sell"
    assert len(Order.objects.all()) == 2


@pytest.mark.django_db()
def test_get_all_markets_from_exchange():
    # load all markets
    markets: List[Market] = get_all_markets_from_exchange(exchange_id="binance")

    # load markets from binance
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    # compare loaded markets with binance
    assert len(markets) == len(exchange.markets.values())
