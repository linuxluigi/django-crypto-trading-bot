from decimal import Decimal

import pytest
from django.conf import settings
from django.test import RequestFactory
from django_crypto_trading_bot.trading_bot.models import OHLCV, Account, Market
from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation
from django_crypto_trading_bot.trading_bot.tests.factories import (
    AccountFactory,
    BnbCurrencyFactory,
    BnbEurMarketFactory,
    BuyOrderFactory,
    EurCurrencyFactory,
    MarketFactory,
    OHLCVBnbEurFactory,
    OHLCVTrxBnbFactory,
    SellOrderFactory,
    TrxCurrencyFactory,
)


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def simulation() -> Simulation:
    BnbEurMarketFactory()
    market: Market = MarketFactory()
    return Simulation(markets=[market])


@pytest.fixture
def coin_exchange() -> dict:
    ohlcv_bnb_eur: OHLCV = OHLCVBnbEurFactory()
    ohlcv_trx_bnb: OHLCV = OHLCVTrxBnbFactory()
    return {
        "timestamp": ohlcv_bnb_eur.timestamp,
        "currency": {
            "EUR": {"price": Decimal(1), "base_currency": EurCurrencyFactory()},
            "BNB": {
                "price": ohlcv_bnb_eur.closing_price,
                "base_currency": BnbCurrencyFactory(),
            },
            "TRX": {
                "price": ohlcv_trx_bnb.closing_price * ohlcv_bnb_eur.closing_price,
                "base_currency": TrxCurrencyFactory(),
            },
        },
    }
