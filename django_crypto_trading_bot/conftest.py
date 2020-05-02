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
from django_crypto_trading_bot.users.tests.factories import UserFactory


@pytest.fixture
def trade_logic_sell() -> TradeLogic:
    return TradeLogic(order=SellOrderFactory())


@pytest.fixture
def trade_logic_buy() -> TradeLogic:
    return TradeLogic(order=BuyOrderFactory())


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def simulation() -> Simulation:
    account: Account = AccountFactory()
    market: Market = MarketFactory()
    return Simulation(account=account, markets=[market], history_days=365, day_span=30)


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
