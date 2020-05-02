from decimal import Decimal
from enum import Enum
from typing import List, Optional

from django_crypto_trading_bot.trading_bot.models import Market


class Side(Enum):
    BUY = 0
    SELL = 1


class SimulationOrder:
    def __init__(self, price: Decimal, amount: Decimal, side: Side):
        self.price: Decimal = price
        self.amount: Decimal = amount
        self.side: Side = side
        self.done: bool = False


class SimulationBot:
    """Bot simulation class
    """

    def __init__(self, market: Market, day_span: int, min_profit: int):
        self.market: Market = market
        self.day_span: int = day_span
        self.min_profit: int = min_profit
        self.orders: List[SimulationOrder] = []
        self.trade_counter: int = 0

        self.base_amount: Decimal = Decimal(0)
        self.quote_amount: Decimal = Decimal(0)

    def init_order(self, quote_amount: Decimal, ticker_history: List[dict]):
        """init order

        Arguments:
            quote_amount {Decimal} -- amount of quote currency
            ticker_history {dict} -- ticker history for day span
        """

        low: float = ticker_history[0][3]
        for ticker in ticker_history:
            if ticker[3] < low:
                low = ticker[3]

        self.orders.append(
            SimulationOrder(price=Decimal(low), amount=quote_amount, side=Side.BUY,)
        )

    def update_orders(self, ticker_history: List[dict]):
        last_ticker: dict = ticker_history[-1]
        trade_price: Decimal = Decimal(
            (last_ticker[1] + last_ticker[2] + last_ticker[3] + last_ticker[4]) / 4
        )

        low: Optional[float] = None
        high: Optional[float] = None

        for order_id in range(0, len(self.orders)):
            order: SimulationOrder = self.orders[order_id]

            if order.done:
                continue

            if order.side == Side.BUY:
                if order.price <= trade_price:
                    if not high:
                        high = order.price + order.price * (self.min_profit / 100)
                        for ticker in ticker_history:
                            if high < ticker[2]:
                                high = ticker[2]

                    new_amount: Decimal = order.amount / order.price
                    fee: Decimal = new_amount * 0.001
                    self.orders.append(
                        SimulationOrder(
                            price=Decimal(high),
                            amount=new_amount - fee,
                            side=Side.SELL,
                        )
                    )

                    self.orders[order_id].done = True

            else:
                if order.price >= trade_price:
                    if not low:
                        low = order.price - order.price * (self.min_profit / 100)
                        for ticker in ticker_history:
                            if low < ticker[3]:
                                low = ticker[3]

                    new_amount: Decimal = order.amount * order.price
                    fee: Decimal = new_amount * 0.001
                    self.orders.append(
                        SimulationOrder(
                            price=Decimal(low), amount=new_amount - fee, side=Side.BUY,
                        )
                    )

                    self.orders[order_id].done = True

    def count_amounts(self):
        for order in self.orders:
            if order.done:
                continue

            if order.side == Side.BUY:
                self.quote_amount += order.amount
            else:
                self.base_amount += order.amount

    def __str__(self):
        return "{} | day_span {} | min_profit {}".format(
            self.market.symbol, self.day_span, self.min_profit
        )
