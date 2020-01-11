from decimal import Decimal
from django_crypto_trading_bot.trading_bot.models import Market, Bot, Order
from django_crypto_trading_bot.trading_bot.api.order import create_order
from typing import List
from ccxt.base.exchange import Exchange
from .exceptions import InsufficientTradingAmount, TickerWasNotSet


class TradeLogic:
    """
    create trade logic
    """

    def __init__(
        self,
        order: Order,
        ticker_low: Decimal = Decimal(-1.0),
        ticker_high: Decimal = Decimal(0),
    ):
        """
        Create trading logic
        
        Arguments:
            order {Order} -- fulfilled order
        
        Keyword Arguments:
            ticker_low {Decimal} -- Ticker low price (default: {Decimal(-1.0)})
            ticker_high {Decimal} -- Ticker high price (default: {Decimal(0)})
        """
        self.order: Order = order
        self.amount_buy: Decimal = Decimal(0)
        self.amount_sell: Decimal = Decimal(0)

        # get client
        self.client: Exchange = order.bot.account.get_account_client()

        # ticker
        self.ticker_low: Decimal = ticker_low
        self.ticker_high: Decimal = ticker_high

    def create_reorder(self, simulation: bool = False) -> Order:
        """
        create a reorder if possible
        
        Keyword Arguments:
            simulation {bool} -- if true, it will not create a real order (default: {False})
        
        Raises:
            InsufficientTradingAmount: raise when the current order has insufficient trading amount
            TickerWasNotSet: raise when try to create a reader with to set a ticker first
        
        Returns:
            Order -- new reorder
        """

        if self.ticker_low <= Decimal(0) and self.ticker_high <= Decimal(0):
            raise TickerWasNotSet("Ticker was not set!")

        trade_price: Decimal = self.filter_price(self.trade_price())
        retrade_amount: Decimal = self.filter_amount(
            self.retrade_amount(price=trade_price)
        )
        if self.order.side == Order.SIDE_BUY:
            side: str = Order.SIDE_SELL
        else:
            side: str = Order.SIDE_BUY

        if retrade_amount <= Decimal(0):
            raise InsufficientTradingAmount(
                "Insufficient trading amount for {}".format(self.order.order_id)
            )

        reorder: Order = create_order(
            amount=retrade_amount,
            price=trade_price,
            side=side,
            bot=self.order.bot,
            isTestOrder=simulation,
        )

        self.order.reorder = reorder
        self.order.save()

        return reorder

    def min_profit_price(self) -> Decimal:
        """
        set min profit for retrade
        """
        min_profit: Decimal = Decimal(
            self.order.price / 100 * self.order.bot.min_profit
        )

        # set min buy profit
        if self.order.side == Order.SIDE_SELL:
            return self.order.price - min_profit

        # set min sell profit
        return self.order.price + min_profit

    def trade_price(self) -> Decimal:
        # sell price
        if self.order.side == Order.SIDE_BUY:
            if self.ticker_high < self.min_profit_price():
                return self.min_profit_price()
            else:
                return self.ticker_high

        # buy price
        if self.ticker_low > self.min_profit_price():
            return self.min_profit_price()
        else:
            return self.ticker_low

    def set_min_max_price(self, price: Decimal) -> Decimal:
        """
        set the buy & sell min & max prices
        """
        if price < self.order.bot.market.limits_price_min:
            price = self.order.bot.market.limits_price_min
        if price > self.order.bot.market.limits_price_max:
            price = self.order.bot.market.limits_price_max
        return price

    def set_min_max_order_amount(self, amount: Decimal) -> Decimal:
        """
        set the buy & sell min & max amount
        """
        if amount < self.order.bot.market.limits_amount_min:
            amount = 0
        if amount > self.order.bot.market.limits_amount_max:
            amount = self.order.bot.market.limits_amount_max
        return amount

    def retrade_amount(self, price: Decimal) -> Decimal:
        """
        get retrade amount
        
        Arguments:
            price {Decimal} -- price for a new buy order
        
        Returns:
            Decimal -- retrade amount
        """
        if self.order.side == Order.SIDE_BUY:
            return Decimal(self.order.base_amount())
        return Decimal(self.order.quote_amount() / price)

    def filter_amount(self, amount: Decimal) -> Decimal:
        """
        Convert amount to a valid market order amount
        
        Arguments:
            amount {Decimal} -- amount to filter
        
        Returns:
            Decimal -- tradeable amount
        """
        precision_amount: int = self.order.bot.market.precision_amount
        rest: Decimal = amount % round(
            self.order.bot.market.limits_amount_min, precision_amount
        )
        rest_amount: Decimal = amount - rest

        amount = Decimal(amount - (amount % self.order.bot.market.limits_amount_min))

        return self.set_min_max_order_amount(
            amount=round(rest_amount, precision_amount)
        )

    def filter_price(self, price: Decimal) -> Decimal:
        """
        Convert price to a valid market order price
        
        Arguments:
            amount {Decimal} -- price to filter
        
        Returns:
            Decimal -- tradeable price
        """

        precision_price: int = self.order.bot.market.precision_price
        rest: Decimal = price % round(
            self.order.bot.market.limits_price_min, precision_price
        )
        rest_price: Decimal = price - rest

        if rest_price <= 0:
            return Decimal(0)

        return self.set_min_max_price(price=round(rest_price, precision_price))

    def setup_ticker(self) -> None:
        """
        get low & high from ticker
        """
        since = (
            self.client.milliseconds() - 1000 * 60 * 60 * 24 * self.order.bot.day_span
        )
        ticker: dict = self.client.fetch_ohlcv(
            symbol=self.order.bot.market.symbol, timeframe="1d", since=since, limit=None
        )

        for tick in ticker:
            tick_high: Decimal = Decimal(tick[2])
            tick_low: Decimal = Decimal(tick[3])
            # set high
            if self.ticker_high < tick_high:
                self.ticker_high = tick_high

            if self.ticker_low == -1:
                self.ticker_low = tick_low
            else:
                if self.ticker_low > tick_low:
                    self.ticker_low = tick_low
