from decimal import Decimal

import pytest
from django.conf import settings
from django.test import RequestFactory

from django_crypto_trading_bot.trading_bot.models import Account, Market
from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation
from django_crypto_trading_bot.trading_bot.tests.factories import (
    AccountFactory,
    BnbCurrencyFactory,
    BuyOrderFactory,
    EurCurrencyFactory,
    MarketFactory,
    SellOrderFactory,
    TrxCurrencyFactory,
)
from django_crypto_trading_bot.trading_bot.trade_logic import TradeLogic


@pytest.fixture
def trade_logic_sell() -> TradeLogic:
    return TradeLogic(order=SellOrderFactory())


@pytest.fixture
def trade_logic_buy() -> TradeLogic:
    return TradeLogic(order=BuyOrderFactory())


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def simulation() -> Simulation:
    market: Market = MarketFactory()
    return Simulation(markets=[market])


@pytest.fixture
def coin_exchange() -> dict:
    return {
        "timestamp": 1588280400000,
        "currency": {
            "EUR": {"price": Decimal(1), "base_currency": EurCurrencyFactory()},
            "BNB": {"price": Decimal(15.7987), "base_currency": BnbCurrencyFactory()},
            "TRX": {
                "price": Decimal(0.000896) * Decimal(15.7987),
                "base_currency": TrxCurrencyFactory(),
            },
        },
    }
