import pytest
from django.conf import settings
from django.test import RequestFactory

from django_crypto_trading_bot.users.tests.factories import UserFactory
from django_crypto_trading_bot.trading_bot.trade_logic import TradeLogic
from django_crypto_trading_bot.trading_bot.tests.factories import (
    BuyOrderFactory,
    SellOrderFactory,
)


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
