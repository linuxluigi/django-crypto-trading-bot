from decimal import Decimal
from typing import Dict, List, Optional

from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.api.market import get_all_markets_from_exchange
from django_crypto_trading_bot.trading_bot.models import Account, Currency, Market
from django_crypto_trading_bot.trading_bot.simulation.bot import SimulationBot


class Simulation:
    def __init__(
        self,
        account: Account,
        markets: Optional[List[Market]] = None,
        amount_eur: Decimal = Decimal(5),
        day_span: int = 30,
        min_profit: int = 30,
        history_days: int = 365,
    ):
        """
        Simulate trading without taking any real order, works only with binance
        
        Arguments:
            account {Account} -- Test Account
        
        Keyword Arguments:
            markets {Optional[List[Market]]} -- Marktes to test, if none test on all markets on the exchange (default: {None})
            amount_eur {Decimal} -- trading amount for each bot (default: {Decimal(15)})
            day_span {int} -- day_span for the bots (default: {30})
            min_profit {int} -- min profit in percent (default: {1})
            history_days {int} -- simulate the history in days (default: {365})
        """

        self.account: Account = account
        self.amount_eur: Decimal = amount_eur
        self.day_span: int = day_span
        self.min_profit: int = min_profit
        self.exchange: Exchange = account.get_account_client()
        self.history_days = history_days

        if markets:
            self.markets = markets
        else:
            self.markets = get_all_markets_from_exchange(exchange_id=self.exchange.id)

        # coin prices
        self.coin_prices = {}

        # simulation bots
        self.bots: List[SimulationBot] = []

        # ticker_history
        self.ticker_history: Dict[str, dict] = {}

    def init_bots_ticker(self):
        # fill bot
        for market in self.markets:
            self.bots.append(
                SimulationBot(
                    market=market, day_span=self.day_span, min_profit=self.min_profit
                )
            )

        # fill ticker_history
        for market in self.markets:
            self.ticker_history[market.symbol] = self.get_tickert(
                market=market, day_span=self.day_span, history_days=self.history_days
            )

    def get_tickert(self, market: Market, day_span: int, history_days: int) -> dict:
        """
        get ticker for market (1 minute candles
        
        Arguments:
            market {[Market]} -- ticker market
            day_span {[int]} -- bot day_span
            history_days {[int]} -- how many days ticker should go back in time
        
        Returns:
            dict -- ticker of the last history_days in 1 min candles
        """
        exchange_time: int = self.exchange.milliseconds()

        # milliseconds (1000) * seconds (60) * minutes (60) * hours (24) = 86.400.000
        simulate_time_from: int = exchange_time - 86400000 * (history_days + day_span)

        candles: List[dict] = []
        # 500 1 minutes candle = milliseconds (1000) * seconds (60) * 500 candles = 30.000.000
        for start_time in range(simulate_time_from, exchange_time, 30000000):
            candles += self.exchange.fetch_ohlcv(
                symbol=market.symbol, timeframe="1m", since=start_time, limit=500
            )

        return candles

    def coin_2_eur(
        self, currency: Currency, coin_amount: Decimal, request_time: Optional[int] = None
    ) -> Decimal:

        # if coin is EUR
        if currency.short.upper() == "EUR":
            return coin_amount

        if not request_time in self.coin_prices:
            self.coin_prices[request_time] = {}

        if not "BNB" in self.coin_prices[request_time]:
            if request_time:
                bnb_eur_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="BNB/EUR", timeframe="1m", since=request_time, limit=1
                )[0]
            else:
                bnb_eur_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="BNB/EUR", timeframe="1m", limit=1
                )[0]
            self.coin_prices[request_time]["BNB"] = Decimal(bnb_eur_candle[4])

        # if coin is BNB
        if currency.short.upper() == "BNB":
            return coin_amount * self.coin_prices[request_time]["BNB"]

        if not currency.short in self.coin_prices[request_time]:
            if request_time:
                currency_bnb_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="{}/BNB".format(currency.short.upper()),
                    timeframe="1m",
                    since=request_time,
                    limit=1,
                )[0]
            else:
                currency_bnb_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="{}/BNB".format(currency.short.upper()),
                    timeframe="1m",
                    limit=1,
                )[0]

            self.coin_prices[request_time][currency.short] = Decimal(
                currency_bnb_candle[4]
            )

        return (
            coin_amount
            * self.coin_prices[request_time][currency.short]
            * self.coin_prices[request_time]["BNB"]
        )

    def eur_2_coin(
        self, currency: Currency, eur_amount: Decimal, request_time: Optional[int] = None
    ) -> Decimal:
        # if coin is EUR
        if currency.short.upper() == "EUR":
            return eur_amount

        if not request_time in self.coin_prices:
            self.coin_prices[request_time] = {}

        if not "BNB" in self.coin_prices[request_time]:
            if request_time:
                bnb_eur_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="BNB/EUR", timeframe="1m", since=request_time, limit=1
                )[0]
            else:
                bnb_eur_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="BNB/EUR", timeframe="1m", limit=1
                )[0]

            self.coin_prices[request_time]["BNB"] = Decimal(bnb_eur_candle[4])

        # if coin is BNB
        if currency.short.upper() == "BNB":
            return eur_amount / self.coin_prices[request_time]["BNB"]

        if not currency.short in self.coin_prices[request_time]:
            if request_time:
                currency_bnb_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="{}/BNB".format(currency.short.upper()),
                    timeframe="1m",
                    since=request_time,
                    limit=1,
                )[0]
            else:
                currency_bnb_candle: dict = self.exchange.fetch_ohlcv(
                    symbol="{}/BNB".format(currency.short.upper()),
                    timeframe="1m",
                    limit=1,
                )[0]

            self.coin_prices[request_time][currency.short] = Decimal(
                currency_bnb_candle[4]
            )

        return (
            eur_amount
            / self.coin_prices[request_time][currency.short]
            / self.coin_prices[request_time]["BNB"]
        )

    def run_simulation(self):
        ticker_day_span: int = 1440 * self.day_span

        bot: SimulationBot
        for bot in self.bots:

            quote_amount: Decimal = self.eur_2_coin(
                currency=bot.market.quote,
                eur_amount=self.amount_eur,
                request_time=self.ticker_history[bot.market.symbol][0][0],
            )

            bot.init_order(
                quote_amount=quote_amount,
                ticker_history=self.ticker_history[bot.market.symbol][
                    0:ticker_day_span
                ],
            )

            for start in range(0, ticker_day_span - ticker_day_span):
                bot.update_orders(
                    ticker_history=self.ticker_history[bot.market.symbol][
                        start : ticker_day_span + start
                    ]
                )

            bot.count_amounts()

            bot_eur_value: Decimal = self.coin_2_eur(
                currency=bot.market.quote, coin_amount=bot.quote_amount
            )
            bot_eur_value += self.coin_2_eur(
                currency=bot.market.base, coin_amount=bot.base_amount
            )

            print(
                "{} | from {:0.4f}€ to {:0.4f}€ | day_span {} | history {}".format(
                    bot.market,
                    self.amount_eur,
                    bot_eur_value,
                    self.day_span,
                    self.history_days,
                )
            )
