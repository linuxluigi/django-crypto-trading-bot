from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional

from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
)
from django_crypto_trading_bot.trading_bot.models import (
    Account,
    Currency,
    Market,
    OHLCV,
    Exchanges,
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
        self.day_span: int = day_span
        self.min_profit: int = min_profit
        self.exchange: Exchange = account.get_account_client()
        self.history_days = history_days
        self.timeframe: OHLCV.Timeframes = timeframe
        self.eur_currency: Currency = Currency.objects.get_or_create(short="EUR")
        self.bnb_currency: Currency = Currency.objects.get_or_create(short="BNB")
        self.bnb_eur_market: Market = Market.objects.get(
            base=self.bnb_currency, quote=self.eur_currency, exchange=Exchanges.BINANCE
        )

        if markets:
            self.markets = markets
        else:
            self.markets = Market.objects.filter(active=True)

    def coin_2_eur(
        self, currency: Currency, coin_amount: Decimal, request_time: datetime,
    ) -> Decimal:

        # if coin is EUR
        if currency == self.eur_currency:
            return coin_amount

        bnb_OHLCV: OHLCV = OHLCV.get(
            market=self.bnb_eur_market, timeframe=self.timeframe, timestamp=request_time
        )

        # if coin is BNB
        if currency == self.bnb_currency:
            return coin_amount * bnb_OHLCV.closing_price

        market: Market = Market.objects.get(
            base=currency, quote=self.bnb_currency, exchange=Exchanges.BINANCE
        )
        coin_OHLCV: OHLCV = OHLCV.get(
            market=market, timeframe=self.timeframe, timestamp=request_time
        )
        eur_price: Decimal = eur_OHLCV.closing_price

        return coin_amount * coin_OHLCV.closing_price * bnb_OHLCV.closing_price
