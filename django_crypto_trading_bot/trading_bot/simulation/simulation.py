from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
)
from django_crypto_trading_bot.trading_bot.exceptions import (
    SimulationMissCurrency,
    SimulationMissMarket,
)
from django_crypto_trading_bot.trading_bot.models import (
    OHLCV,
    Account,
    Currency,
    Exchanges,
    Market,
)
from django_crypto_trading_bot.trading_bot.simulation.bot import SimulationBot


class Simulation:
    def __init__(
        self,
        markets: Optional[List[Market]] = None,
        amount_eur: Decimal = Decimal(5),
        day_span: List[int] = [30],
        min_profit: List[int] = [1],
        history_days: int = 365,
        timeframe: OHLCV.Timeframes = OHLCV.Timeframes.MINUTE_1,
    ):

        self.amount_eur: Decimal = amount_eur
        self.day_span: List[int] = day_span
        self.min_profit: List[int] = min_profit
        self.history_days: int = history_days
        self.timeframe: OHLCV.Timeframes = timeframe

        try:
            self.eur_currency: Currency = Currency.objects.get(short="EUR")
        except Currency.DoesNotExist:
            raise SimulationMissCurrency("EUR currency is missing!")
        try:
            self.bnb_currency: Currency = Currency.objects.get(short="BNB")
        except Currency.DoesNotExist:
            raise SimulationMissCurrency("BNB currency is missing!")

        try:
            self.bnb_eur_market: Market = Market.objects.get(
                base=self.bnb_currency,
                quote=self.eur_currency,
                exchange=Exchanges.BINANCE,
            )
        except Market.DoesNotExist:
            raise SimulationMissMarket("BNB/EUR currency is missing!")

        if markets:
            self.markets = markets
        else:
            self.markets = list(Market.objects.filter(active=True))

    def coin_2_eur(
        self, currency: Currency, coin_amount: Decimal, request_time: datetime,
    ) -> Decimal:

        # if coin is EUR
        if currency == self.eur_currency:
            return coin_amount

        bnb_OHLCV: OHLCV = OHLCV.objects.get(
            market=self.bnb_eur_market, timeframe=self.timeframe, timestamp=request_time
        )

        # if coin is BNB
        if currency == self.bnb_currency:
            return coin_amount * bnb_OHLCV.closing_price

        market: Market = Market.objects.get(
            base=currency, quote=self.bnb_currency, exchange=Exchanges.BINANCE
        )
        coin_OHLCV: OHLCV = OHLCV.objects.get(
            market=market, timeframe=self.timeframe, timestamp=request_time
        )
        eur_price: Decimal = coin_OHLCV.closing_price

        return coin_amount * coin_OHLCV.closing_price * bnb_OHLCV.closing_price

    def eur_2_coin(
        self, currency: Currency, eur_amount: Decimal, request_time: datetime,
    ) -> Decimal:
        # if coin is EUR
        if currency == self.eur_currency:
            return eur_amount

        bnb_OHLCV: OHLCV = OHLCV.objects.get(
            market=self.bnb_eur_market, timeframe=self.timeframe, timestamp=request_time
        )

        # if coin is BNB
        if currency == self.bnb_currency:
            return eur_amount / bnb_OHLCV.closing_price

        market: Market = Market.objects.get(
            base=currency, quote=self.bnb_currency, exchange=Exchanges.BINANCE
        )
        coin_OHLCV: OHLCV = OHLCV.objects.get(
            market=market, timeframe=self.timeframe, timestamp=request_time
        )
        eur_price: Decimal = coin_OHLCV.closing_price

        return eur_amount / eur_price / bnb_OHLCV.closing_price
