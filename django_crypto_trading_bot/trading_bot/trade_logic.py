from decimal import Decimal
from django_crypto_trading_bot.trading_bot.models import Market, Bot, Order
from typing import List
from ccxt.base.exchange import Exchange


class TradeLogic:
    """
    create trade logic
    """

    def __init__(self, order: Order):
        """
        Create trading logic
        
        Arguments:
            order {Order} -- [description]
        """
        self.order: Order = order
        self.amount_buy: Decimal = Decimal(0)
        self.amount_sell: Decimal = Decimal(0)

        # get client
        self.client: Exchange = order.bot.account.get_account_client()

        # ticker
        self.low: Decimal = Decimal(-1.0)
        self.high: Decimal = Decimal(0.0)

    def min_profit_price(self) -> Decimal:
        """
        set min profit for retrade
        """
        min_profit: Decimal = self.order.price / 100 * self.order.bot.min_profit

        # set min buy profit
        if self.order.side == Order.SIDE_SELL:
            return self.order.price - min_profit

        # set min sell profit
        return self.order.price + min_profit

    def trade_price(self) -> Decimal:
        # sell price
        if self.order.side == Order.SIDE_BUY:
            if self.high < self.min_profit_price():
                return self.min_profit_price()
            else:
                return self.high

        # buy price
        if self.low > self.min_profit_price():
            return self.min_profit_price()
        else:
            return self.low

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
            if self.high < tick_high:
                self.high = tick_high

            if self.low == -1:
                self.low = tick_low
            else:
                if self.low > tick_low:
                    self.low = tick_low
