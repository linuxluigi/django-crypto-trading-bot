import logging
from datetime import datetime, timedelta
from decimal import Decimal
from functools import partial
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Optional

from ccxt.base.exchange import Exchange
from django.utils import timezone

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
    QUOTE_AMOUNT: Decimal = Decimal(100)

    def __init__(
        self,
        markets: Optional[List[Market]] = None,
        quote_amount: Decimal = Decimal(5),
        day_span: List[int] = [30],
        min_profit: List[float] = [1],
        history_days: int = 365,
        timeframe: OHLCV.Timeframes = OHLCV.Timeframes.DAY_1,
        threads: int = 1,
    ):

        self.quote_amount: Decimal = quote_amount
        self.day_span: List[int] = day_span
        self.day_span.sort()
        self.min_profit: List[float] = min_profit
        self.min_profit.sort()
        self.history_days: int = history_days
        self.timeframe: OHLCV.Timeframes = timeframe
        self.threads: int = threads

        if markets:
            self.markets = markets
        else:
            self.markets = list(Market.objects.filter(active=True))

    @staticmethod
    def simulate_bot(
        bot: SimulationBot, candles: List[OHLCV], history_days: int
    ) -> SimulationBot:
        logger.info("Simulate {} bot".format(bot))

        return_of_investments: List[Decimal] = list()

        # create candles chunk for history_days (skip first 10 days)
        for candle_start in range(10, len(candles) - history_days):
            # return_of_investments.append(bot.get_roi(last_candle=candle_chunk[-1]))
            return_of_investments.append(
                bot.simulate_bot(
                    quote_amount=Simulation.QUOTE_AMOUNT,
                    ticker_history=candles[candle_start : candle_start + history_days],
                )
            )

        # sort roi list
        return_of_investments.sort()

        # sum of all return_of_investments
        sum_return_of_investments: Decimal = Decimal(0)
        for roi in return_of_investments:
            sum_return_of_investments += roi

        # average roi for all simulations
        return_of_investment_average: Decimal = sum_return_of_investments / len(
            return_of_investments
        )

        # average end quote amount
        end_quote_amount: Decimal = sum_return_of_investments * return_of_investment_average / 100

        # save simulation result
        simulation: SimulationDB = SimulationDB.objects.create(
            market=bot.market,
            day_span=bot.day_span,
            min_profit=bot.min_profit,
            history_days=history_days,
            start_simulation=candles[0].timestamp,
            end_simulation=candles[-1].timestamp,
            simulation_amount=len(return_of_investments),
            start_amount_quote=Simulation.QUOTE_AMOUNT,
            end_amount_quote_average=end_quote_amount,
            roi_min=return_of_investments[0],
            roi_average=return_of_investment_average,
            roi_max=return_of_investments[-1],
        )

        logger.info(simulation)

        return bot

    def run_simulation(self):
        for market in self.markets:
            logger.info("Simulate {} market".format(market))

            # create simulation bots
            bots: List[SimulationBot] = list()
            for min_profit in self.min_profit:
                bots.append(
                    SimulationBot(market=market, day_span=0, min_profit=min_profit)
                )

            # get all candles of the market for the last 4 years except the first 100
            time_threshold = timezone.now() - timedelta(days=365 * 4)
            candles: List[OHLCV] = list(
                OHLCV.objects.filter(
                    market=market,
                    timeframe=self.timeframe,
                    timestamp__gte=time_threshold,
                ).order_by("timestamp")[100:]
            )

            # Make the Pool of workers
            pool = ThreadPool(self.threads)

            # run simulation for each bot
            bots = pool.map(
                partial(
                    Simulation.simulate_bot,
                    candles=candles,
                    history_days=self.history_days,
                ),
                bots,
            )

            # Close the pool and wait for the work to finish
            pool.close()
            pool.join()
