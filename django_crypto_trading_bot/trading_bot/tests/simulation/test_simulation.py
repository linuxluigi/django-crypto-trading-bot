from datetime import datetime, timedelta
from decimal import Decimal, getcontext

import pytest
from django_crypto_trading_bot.trading_bot.exceptions import (
    SimulationMissCurrency,
    SimulationMissMarket,
)
from django_crypto_trading_bot.trading_bot.models import Account, Market
from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation
from django_crypto_trading_bot.trading_bot.tests.factories import (
    BnbCurrencyFactory,
    BnbEurMarketFactory,
    EurCurrencyFactory,
)


@pytest.mark.django_db()
def test_init():
    # check if a error will raise, on missing currencies
    with pytest.raises(SimulationMissCurrency):
        # EUR missing
        Simulation()

    # create eur currency
    EurCurrencyFactory()

    with pytest.raises(SimulationMissCurrency):
        # BNB missing
        Simulation()

    BnbCurrencyFactory()

    with pytest.raises(SimulationMissMarket):
        # BNB/EUR market is missing
        Simulation()

    # check if simulation use the target market
    market: Market = BnbEurMarketFactory()

    simulation = Simulation()
    assert simulation.markets[0] == market


@pytest.mark.django_db()
def test_coin_2_eur(simulation: Simulation, coin_exchange: dict):
    # set all decimal numbers a precision of 8
    getcontext().prec = 8

    for key, value in coin_exchange["currency"].items():
        assert simulation.coin_2_eur(
            currency=value["base_currency"],
            coin_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == value["price"] * Decimal(10)


@pytest.mark.django_db()
def test_eur_2_coin(simulation: Simulation, coin_exchange: dict):
    # set all decimal numbers a precision of 8
    getcontext().prec = 8

    for key, value in coin_exchange["currency"].items():
        assert simulation.eur_2_coin(
            currency=value["base_currency"],
            eur_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == pytest.approx(Decimal(10) / value["price"])
