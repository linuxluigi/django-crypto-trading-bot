import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
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

logger = logging.getLogger(__name__)


class Simulation:
    def __init__(
        self,
        markets: Optional[List[Market]] = None,
        quote_amount: Decimal = Decimal(5),
        day_span: List[int] = [30],
        min_profit: List[float] = [1],
        history_days: int = 365,
        timeframe: OHLCV.Timeframes = OHLCV.Timeframes.MINUTE_1,
    ):

        self.quote_amount: Decimal = quote_amount
        self.day_span: List[int] = day_span
        self.day_span.sort()
        self.min_profit: List[float] = min_profit
        self.min_profit.sort()
        self.history_days: int = history_days
        self.timeframe: OHLCV.Timeframes = timeframe

        if markets:
            self.markets = markets
        else:
            self.markets = list(Market.objects.filter(active=True))

    # def coin_2_eur(
    #     self, currency: Currency, coin_amount: Decimal, request_time: datetime,
    # ) -> Decimal:

    #     # if coin is EUR
    #     if currency == self.eur_currency:
    #         return coin_amount

    #     bnb_OHLCV: OHLCV = OHLCV.objects.get(
    #         market=self.bnb_eur_market, timeframe=self.timeframe, timestamp=request_time
    #     )

    #     # if coin is BNB
    #     if currency == self.bnb_currency:
    #         return coin_amount * bnb_OHLCV.closing_price

    #     market: Market = Market.objects.get(
    #         base=currency, quote=self.bnb_currency, exchange=Exchanges.BINANCE
    #     )
    #     coin_OHLCV: OHLCV = OHLCV.objects.get(
    #         market=market, timeframe=self.timeframe, timestamp=request_time
    #     )
    #     eur_price: Decimal = coin_OHLCV.closing_price

    #     return coin_amount * coin_OHLCV.closing_price * bnb_OHLCV.closing_price

    # def eur_2_coin(
    #     self, currency: Currency, eur_amount: Decimal, request_time: datetime,
    # ) -> Decimal:
    #     # if coin is EUR
    #     if currency == self.eur_currency:
    #         return eur_amount

    #     bnb_OHLCV: OHLCV = OHLCV.objects.get(
    #         market=self.bnb_eur_market, timeframe=self.timeframe, timestamp=request_time
    #     )

    #     # if coin is BNB
    #     if currency == self.bnb_currency:
    #         return eur_amount / bnb_OHLCV.closing_price

    #     market: Market = Market.objects.get(
    #         base=currency, quote=self.bnb_currency, exchange=Exchanges.BINANCE
    #     )
    #     coin_OHLCV: OHLCV = OHLCV.objects.get(
    #         market=market, timeframe=self.timeframe, timestamp=request_time
    #     )
    #     eur_price: Decimal = coin_OHLCV.closing_price

    #     return eur_amount / eur_price / bnb_OHLCV.closing_price

    def run_simulation(self):
        history_amount: int = 1440 * self.history_days

        for market in self.markets:
            logger.info("Simulate {} market".format(market))
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

            # get all candles of the market except the first 100
            candles: List[OHLCV] = list(
                OHLCV.objects.filter(market=market, timeframe=self.timeframe).order_by(
                    "timestamp"
                )[100:]
            )

            # run simulation for each bot
            bot: SimulationBot
            for bot in bots:
                logger.info("Simulate {} bot".format(bot))

                # the candle amount for the current bot
                # 1.440 = 60 minutes * 24 hours
                iteration_amount: int = 1440 * (bot.day_span + self.history_days)

                # candle amount for day_span
                day_span_amount: int = 1440 * bot.day_span

                # create candles chunk for history_days + day_span where
                # todo
                for candle_start in range(0, len(candles) - iteration_amount, 5000):
                    # candle chuck for current bot
                    candle_chunk: List[OHLCV] = candles[
                        candle_start : candle_start + iteration_amount
                    ]

                    # init bot
                    bot.init_order(
                        quote_amount=self.quote_amount,
                        ticker_history=candle_chunk[0:day_span_amount],
                    )

                    # iterate through every candle for current bot
                    for start in range(0, len(candle_chunk) - day_span_amount):
                        bot.update_orders(
                            ticker_history=candle_chunk[start : day_span_amount + start]
                        )

                    # count assets
                    results[bot.day_span][bot.min_profit].append(
                        bot.count_amounts(last_candle=candle_chunk[-1])
                    )

            # evaluate results
            for day_span_key, day_span_value in results.items():
                for min_profit_key, value in day_span_value.items():

                    if not len(value):
                        continue

                    end_amount_min: Decimal = value[0]
                    end_amount_max: Decimal = value[0]
                    all_amounts: Decimal = Decimal(0)

                    for amount in value:
                        all_amounts += amount
                        if amount < end_amount_min:
                            end_amount_min = amount
                        if amount > end_amount_max:
                            end_amount_max = amount

                    average_amount: Decimal = all_amounts / len(value)

                    simulation: SimulationDB = SimulationDB.objects.create(
                        market=market,
                        day_span=day_span_key,
                        min_profit=min_profit_key,
                        history_days=self.history_days,
                        start_simulation=candles[0].timestamp,
                        end_simulation=candles[-1].timestamp,
                        simulation_amount=len(value),
                        start_amount_quote=self.quote_amount,
                        end_amount_quote_average=average_amount,
                        roi_min=(end_amount_min - self.quote_amount)
                        / self.quote_amount,
                        roi_average=(average_amount - self.quote_amount)
                        / self.quote_amount,
                        roi_max=(end_amount_max - self.quote_amount)
                        / self.quote_amount,
                    )

                    logger.info(simulation)
