from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from django_crypto_trading_bot.trading_bot.models import Account, Market
from django_crypto_trading_bot.trading_bot.simulation.simulation import \
    Simulation
from django_crypto_trading_bot.trading_bot.tests.factories import (
    AccountFactory, BnbCurrencyFactory, EurCurrencyFactory, MarketFactory,
    TrxCurrencyFactory)


@pytest.mark.django_db()
def test_get_tickert(simulation: Simulation):
    # get ticker

    ticker_1_start: datetime = datetime.now()
    ticker_1: dict = simulation.get_tickert(
        market=simulation.markets[0], day_span=1, history_days=0
    )
    # days (1+0) * hours (24) * minutes (60) = 1.440
    ticker_1_working_time: timedelta = datetime.now() - ticker_1_start
    assert len(ticker_1) >= 1440
    assert len(ticker_1) <= 1440 + int(ticker_1_working_time.seconds / 60)

    ticker_2_start: datetime = datetime.now()
    ticker_2: dict = simulation.get_tickert(
        market=simulation.markets[0], day_span=10, history_days=0
    )
    # days (10+0) * hours (24) * minutes (60) = 14.400
    ticker_2_working_time: timedelta = datetime.now() - ticker_2_start
    assert len(ticker_2) >= 14400
    assert len(ticker_1) <= 1440 + int(ticker_2_working_time.seconds / 60)

    ticker_3_start: datetime = datetime.now()
    ticker_3: dict = simulation.get_tickert(
        market=simulation.markets[0], day_span=5, history_days=3
    )
    # days (5+3) * hours (24) * minutes (60) = 11.520
    ticker_3_working_time: timedelta = datetime.now() - ticker_3_start
    assert len(ticker_3) >= 11520
    assert len(ticker_1) <= 1440 + int(ticker_3_working_time.seconds / 60)


@pytest.mark.django_db()
def test_coin_2_eur(simulation: Simulation, coin_exchange: dict):
    # measure time to process, to control if use the cache, if the request doubles
    process_1_start: datetime = datetime.now()
    for key, value in coin_exchange["currency"].items():
        assert simulation.coin_2_eur(
            currency=value["base_currency"],
            coin_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == value["price"] * Decimal(10)

    process_1_time: timedelta = datetime.now() - process_1_start

    assert (
        simulation.coin_prices[coin_exchange["timestamp"]]["BNB"]
        == coin_exchange["currency"]["BNB"]["price"]
    )

    process_2_start: datetime = datetime.now()
    for key, value in coin_exchange["currency"].items():
        assert simulation.coin_2_eur(
            currency=value["base_currency"],
            coin_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == value["price"] * Decimal(10)

    process_2_time: timedelta = datetime.now() - process_2_start

    assert process_1_time > process_2_time


@pytest.mark.django_db()
def test_eur_2_coin(simulation: Simulation, coin_exchange: dict):
    # measure time to process, to control if use the cache, if the request doubles
    process_1_start: datetime = datetime.now()
    for key, value in coin_exchange["currency"].items():
        assert simulation.eur_2_coin(
            currency=value["base_currency"],
            eur_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == pytest.approx(Decimal(10) / value["price"])

    assert (
        simulation.coin_prices[coin_exchange["timestamp"]]["BNB"]
        == coin_exchange["currency"]["BNB"]["price"]
    )

    process_1_time: timedelta = datetime.now() - process_1_start

    process_2_start: datetime = datetime.now()
    for key, value in coin_exchange["currency"].items():
        assert simulation.eur_2_coin(
            currency=value["base_currency"],
            eur_amount=Decimal(10),
            request_time=coin_exchange["timestamp"],
        ) == pytest.approx(Decimal(10) / value["price"])

    process_2_time: timedelta = datetime.now() - process_2_start

    assert process_1_time > process_2_time


@pytest.mark.django_db()
def test_run(simulation: Simulation):

    # init ticker & bot
    simulation.history_days = 3
    simulation.day_span = 1
    simulation.init_bots_ticker()

    # run simulation
    simulation.run_simulation()
