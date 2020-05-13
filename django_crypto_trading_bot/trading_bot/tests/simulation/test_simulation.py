from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from math import pi, sin
from typing import List

import pytest
import pytz
from django_crypto_trading_bot.trading_bot.models import OHLCV, Account, Market
from django_crypto_trading_bot.trading_bot.models import Simulation as SimulationDB
from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation
from django_crypto_trading_bot.trading_bot.tests.factories import (
    BnbCurrencyFactory,
    BnbEurMarketFactory,
    EurCurrencyFactory,
    MarketFactory,
)


@pytest.mark.django_db()
def test_init():
    # check if simulation use the target market
    market: Market = BnbEurMarketFactory()

    simulation = Simulation()
    assert simulation.markets[0] == market


# @pytest.mark.django_db()
# def test_coin_2_eur(simulation: Simulation, coin_exchange: dict):
#     # set all decimal numbers a precision of 8
#     getcontext().prec = 8

#     for key, value in coin_exchange["currency"].items():
#         assert simulation.coin_2_eur(
#             currency=value["base_currency"],
#             coin_amount=Decimal(10),
#             request_time=coin_exchange["timestamp"],
#         ) == value["price"] * Decimal(10)


# @pytest.mark.django_db()
# def test_eur_2_coin(simulation: Simulation, coin_exchange: dict):
#     # set all decimal numbers a precision of 8
#     getcontext().prec = 8

#     for key, value in coin_exchange["currency"].items():
#         assert simulation.eur_2_coin(
#             currency=value["base_currency"],
#             eur_amount=Decimal(10),
#             request_time=coin_exchange["timestamp"],
#         ) == pytest.approx(Decimal(10) / value["price"])


@pytest.mark.django_db()
def test_run_simulation():
    # set all decimal numbers a precision of 8
    getcontext().prec = 8

    BnbEurMarketFactory()
    trx_bnb_market: Market = MarketFactory()
    bnb_eur_market: Market = BnbEurMarketFactory()

    # create demo candel for 395 days
    candles: List[OHLCV] = list()
    timestamp: datetime = datetime(
        year=2019, month=1, day=1, tzinfo=pytz.timezone("UTC")
    )
    minute: timedelta = timedelta(minutes=1)

    # 43.200 = 60 minutes * 24 hours * 30 days
    for x in range(0, 43200):
        # set price for each candle
        price: Decimal = Decimal(sin(x))
        if price < 0:
            price = price * -1

        # TRX/BNB
        candles.append(
            OHLCV(
                market=trx_bnb_market,
                timeframe=OHLCV.Timeframes.MINUTE_1,
                timestamp=timestamp,
                open_price=price,
                highest_price=price,
                lowest_price=price,
                closing_price=price,
                volume=price,
            )
        )

        # BNB/EUR
        price = price * Decimal(pi)
        candles.append(
            OHLCV(
                market=bnb_eur_market,
                timeframe=OHLCV.Timeframes.MINUTE_1,
                timestamp=timestamp,
                open_price=price,
                highest_price=price,
                lowest_price=price,
                closing_price=price,
                volume=price,
            )
        )

        timestamp = timestamp + minute

    OHLCV.objects.bulk_create(candles)

    simulation: Simulation = Simulation(
        markets=[trx_bnb_market],
        day_span=[1, 2, 3],
        min_profit=[1, 2, 3],
        history_days=5,
    )
    simulation.run_simulation()

    assert SimulationDB.objects.all().count() == 9
