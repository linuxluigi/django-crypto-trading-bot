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
from django_crypto_trading_bot.trading_bot.models import Simulation as SimulationDB
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
        self.day_span.sort()
        self.min_profit: List[int] = min_profit
        self.min_profit.sort()
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

    def run_simulation(self):
        history_amount: int = 1440 * self.history_days

        for market in self.markets:
            results: dict = {}

            # create simulation bots
            bots: List[SimulationBot] = list()
            for day_span in self.day_span:
                results[day_span] = {}
                for min_profit in self.min_profit:
                    results[day_span][min_profit] = list()
                    bots.append(
                        SimulationBot(
                            market=market, day_span=day_span, min_profit=min_profit
                        )
                    )

            candles: List[OHLCV] = list(
                OHLCV.objects.filter(market=market, timeframe=self.timeframe).order_by(
                    "timestamp"
                )[100:]
            )

            # todo only for timeframe 1 minute
            # 1.440 = 60 minutes * 24 hours
            max_candles: int = len(candles) - 1440 * self.day_span[-1] + 100

            for candle_start in range(0, max_candles, 1000):
                bot: SimulationBot
                for bot in bots:
                    day_span_amount: int = 1440 * bot.day_span
                    ticker_history: List[OHLCV] = candles[
                        candle_start : candle_start + history_amount
                    ]

                    if len(ticker_history) < history_amount:
                        continue

                    quote_amount: Decimal = self.eur_2_coin(
                        currency=bot.market.quote,
                        eur_amount=self.amount_eur,
                        request_time=ticker_history[0].timestamp,
                    )

                    bot.init_order(
                        quote_amount=quote_amount,
                        ticker_history=ticker_history[0:day_span_amount],
                    )

                    for start in range(
                        0, len(ticker_history) - history_amount - day_span_amount
                    ):
                        if (
                            len(ticker_history[start : day_span_amount + start])
                            < history_amount
                        ):
                            break
                        bot.update_orders(
                            ticker_history=ticker_history[
                                start : day_span_amount + start
                            ]
                        )

                    bot.count_amounts()

                    bot_eur_value: Decimal = self.coin_2_eur(
                        currency=bot.market.quote,
                        coin_amount=bot.quote_amount,
                        request_time=ticker_history[-1].timestamp,
                    )
                    bot_eur_value += self.coin_2_eur(
                        currency=bot.market.base,
                        coin_amount=bot.base_amount,
                        request_time=ticker_history[-1].timestamp,
                    )

                    results[bot.day_span][bot.min_profit].append(bot_eur_value)

            for day_span_key in results:
                for min_profit_key in results:
                    end_amount_min: Decimal = results[day_span_key][min_profit_key][0]
                    end_amount_max: Decimal = results[day_span_key][min_profit_key][0]
                    all_amounts: Decimal = 0

                    for amount in results[day_span_key][min_profit_key]:
                        all_amounts += amount
                        if amount < end_amount_min:
                            end_amount_min = amount
                        if amount > end_amount_max:
                            end_amount_max = amount

                    average_amount: Decimal = all_amounts / len(
                        results[day_span_key][min_profit_key]
                    )

                    simulation: SimulationDB = SimulationDB.objects.create(
                        market=market,
                        day_span=day_span_key,
                        min_profit=min_profit_key,
                        history_days=self.history_days,
                        start_simulation=candles[0].timestamp,
                        end_simulation=candles[-1].timestamp,
                        simulation_amount=len(results[day_span_key][min_profit_key]),
                        start_amount_eur=self.amount_eur,
                        end_amount_eur_average=average_amount,
                        roi_min=(end_amount_min - self.amount_eur) / self.amount_eur,
                        roi_average=(average_amount - self.amount_eur)
                        / self.amount_eur,
                        roi_max=(end_amount_max - self.amount_eur) / self.amount_eur,
                    )

                    print(simulation)
