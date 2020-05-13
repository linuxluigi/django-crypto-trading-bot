from decimal import Decimal
from enum import Enum
from typing import List, Optional

from django_crypto_trading_bot.trading_bot.models import OHLCV, Market, Order


class SimulationOrder:
    def __init__(self, price: Decimal, amount: Decimal, side: Order.Side):
        self.price: Decimal = price
        self.amount: Decimal = amount
        self.side: Order.Side = side
        self.done: bool = False


class SimulationBot:
    """Bot simulation class
    """

    def __init__(self, market: Market, day_span: int, min_profit: float):
        self.market: Market = market
        self.day_span: int = day_span
        self.min_profit: float = min_profit
        self.orders: List[SimulationOrder] = []

        self.base_amount: Decimal = Decimal(0)
        self.quote_amount: Decimal = Decimal(0)

    def init_order(self, quote_amount: Decimal, ticker_history: List[OHLCV]):
        """init order

        Arguments:
            quote_amount {Decimal} -- amount of quote currency
            ticker_history {OHLCV} -- ticker history for day span
        """

        # reset old data
        self.orders.clear()
        self.base_amount = Decimal(0)
        self.quote_amount = Decimal(0)

        low: Decimal = ticker_history[0].lowest_price
        for ticker in ticker_history:
            if ticker.lowest_price < low:
                low = ticker.lowest_price

        self.orders.append(
            SimulationOrder(
                price=Decimal(low), amount=quote_amount, side=Order.Side.SIDE_BUY,
            )
        )

    def update_orders(self, ticker_history: List[OHLCV]):
        last_ticker: OHLCV = ticker_history[-1]
        trade_price: Decimal = (
            last_ticker.open_price
            + last_ticker.highest_price
            + last_ticker.lowest_price
            + last_ticker.closing_price
        ) / 4

        low: Optional[Decimal] = None
        high: Optional[Decimal] = None

        for order_id in range(0, len(self.orders)):
            order: SimulationOrder = self.orders[order_id]
            fee: Decimal
            new_amount: Decimal
            ticker: OHLCV

            if order.done:
                continue

            if order.side == Order.Side.SIDE_BUY:
                if order.price <= trade_price:
                    if not high:
                        high = order.price + order.price * (
                            Decimal(self.min_profit) / Decimal(100)
                        )
                        for ticker in ticker_history:
                            if high < ticker.highest_price:
                                high = ticker.highest_price

                    new_amount = order.amount / order.price
                    fee = new_amount * Decimal(0.001)
                    self.orders.append(
                        SimulationOrder(
                            price=Decimal(high),
                            amount=new_amount - fee,
                            side=Order.Side.SIDE_SELL,
                        )
                    )

                    self.orders[order_id].done = True

            else:
                if order.price >= trade_price:
                    if not low:
                        low = order.price - order.price * (
                            Decimal(self.min_profit) / Decimal(100)
                        )
                        for ticker in ticker_history:
                            if low < ticker.lowest_price:
                                low = ticker.lowest_price

                    new_amount = order.amount * order.price
                    fee = new_amount * Decimal(0.001)
                    self.orders.append(
                        SimulationOrder(
                            price=Decimal(low),
                            amount=new_amount - fee,
                            side=Order.Side.SIDE_BUY,
                        )
                    )

                    self.orders[order_id].done = True

    def count_amounts(self, last_candle: OHLCV):
        for order in self.orders:
            if order.done:
                continue

            if order.side == Order.Side.SIDE_BUY:
                self.quote_amount += order.amount
            else:
                self.base_amount += order.amount

        return self.quote_amount + (self.base_amount * last_candle.closing_price)

    def __str__(self):
        return "{} | day_span {} | min_profit {}".format(
            self.market.symbol, self.day_span, self.min_profit
        )
