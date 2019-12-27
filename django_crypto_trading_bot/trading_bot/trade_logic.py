from decimal import Decimal
from django_crypto_trading_bot.trading_bot.models import Market, Bot, Order
from typing import List
from ccxt.base.exchange import Exchange


class TradeLogic:
    """
    create trade logic
    """

    def __init__(self, bot: Bot, max_new_orders: int = 10):
        """
        bot -> Bot model
        max_new_orders -> the maximum amount of new orders
        """
        self.bot: Bot = bot
        self.max_new_orders: int = max_new_orders
        self.amount_buy: Decimal = Decimal(0)
        self.amount_sell: Decimal = Decimal(0)
        self.open_orders: List[Order] = Order.objects.filter(
            status=Order.CLOSED, bot=bot
        )
        self.calc_amount()

        # get client
        self.client: Exchange = bot.account.get_account_client()

        # ticker
        self.low: Decimal = Decimal(-1.0)
        self.high: Decimal = Decimal(0.0)

        # last trade price
        self.last_buy_price: Decimal = None
        self.last_sell_price: Decimal = None
        self.get_last_price()

        # set min profit
        self.min_buy_price: Decimal = None
        self.min_sell_price: Decimal = None
        self.set_min_profit()

        # set re_orders
        self.re_orders: dict = {
            Order.SIDE_BUY: [],
            Order.SIDE_SELL: [],
        }
        self.set_reorder()

    def calc_amount(self):
        """
        calc amount from all closed bot orders
        """
        for order in self.open_orders:
            if order.side == Order.SIDE_BUY:
                self.amount_buy = self.amount_buy + order.order_amount()
            else:
                self.amount_sell = self.amount_sell + order.order_amount()

    def get_last_price(self):
        for order in self.open_orders:
            # set buy orders
            if order.side == Order.SIDE_BUY:
                if not self.last_buy_price:
                    self.last_buy_price = order.price
                if order.price < self.last_buy_price:
                    self.last_buy_price = order.price
            # set sell orders
            else:
                if not self.last_sell_price:
                    self.last_sell_price = order.price
                if order.price > self.last_sell_price:
                    self.last_sell_price = order.price

    def set_min_profit(self):
        """
        set order min profit
        """
        # set min buy profit
        buy_min_profit: Decimal = Decimal(
            self.last_buy_price / 100 * self.bot.min_profit
        )
        self.min_buy_price = self.last_buy_price + buy_min_profit
        self.min_buy_price = self.set_min_max_price(price=self.min_buy_price)

        # set min sell profit
        sell_min_profit: Decimal = Decimal(
            self.last_sell_price / 100 * self.bot.min_profit
        )
        self.min_sell_price = self.last_sell_price + sell_min_profit
        self.min_sell_price = self.set_min_max_price(price=self.min_sell_price)

    def set_min_max_price(self, price: Decimal) -> Decimal:
        """
        set the buy & sell min & max prices
        """
        if price < self.bot.market.limits_price_min:
            price = self.bot.market.limits_price_min
        if price > self.bot.market.limits_price_max:
            price = self.bot.market.limits_price_max
        return price

    def set_min_max_order_amount(self, amount: Decimal) -> Decimal:
        """
        set the buy & sell min & max amount
        """
        if amount < self.bot.market.limits_amount_min:
            amount = 0
        if amount > self.bot.market.limits_amount_max:
            amount = self.bot.market.limits_amount_max
        return amount

    def setup_ticker(self):
        """
        get low & high from ticker
        """
        since = self.client.milliseconds() - 1000 * 60 * 60 * 24 * self.bot.day_span
        ticker: dict = self.client.fetch_ohlcv(
            symbol=self.bot.market.symbol, timeframe="1d", since=since, limit=None
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

    def set_reorder(self):
        pass
