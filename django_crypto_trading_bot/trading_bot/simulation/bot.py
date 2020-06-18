import logging
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from django_crypto_trading_bot.trading_bot.models import OHLCV, Market, Order

logger = logging.getLogger(__name__)


class SimulationOrder:
    def __init__(self, price: Decimal, amount: Decimal, side: Order.Side):
        self.price: Decimal = price
        self.amount: Decimal = amount
        self.side: Order.Side = side
        self.tick_counter: int = 0

    def __str__(self):
        return "{} price | {} amount | {} side | {} tick_counter".format(
            self.price, self.amount, self.side, self.tick_counter
        )


class SimulationBot:
    """Bot simulation class
    """

    def __init__(self, market: Market, day_span: int, min_profit: float):
        self.market: Market = market
        self.day_span: int = day_span
        self.min_profit: float = min_profit

    def simulate_bot(
        self, quote_amount: Decimal, ticker_history: List[OHLCV]
    ) -> Decimal:
        """run bot simulation & return the return of investment

        Args:
            quote_amount {Decimal} -- amount of quote currency
            ticker_history (List[OHLCV]): [description]

        Returns:
            Decimal: return of investment
        """

        order_counter: int = 0

        order: SimulationOrder = SimulationOrder(
            price=ticker_history[0].lowest_price,
            amount=quote_amount,
            side=Order.Side.SIDE_BUY,
        )

        for last_ticker in ticker_history:
            order.tick_counter += 1

            if order.side == Order.Side.SIDE_BUY:
                if order.price <= last_ticker.lowest_price:
                    high: Decimal = order.price + order.price * (
                        Decimal(self.min_profit) / Decimal(100)
                    )

                    if high < self.market.limits_price_max:
                        high = self.market.limits_price_max

                    new_amount = order.amount / order.price
                    fee = new_amount * Decimal(0.001)

                    order.price = Decimal(high)
                    order.amount = new_amount - fee
                    order.side = Order.Side.SIDE_SELL
                    order.tick_counter = 0

            else:
                if order.price >= last_ticker.highest_price:
                    low: Decimal = order.price - order.price * (
                        Decimal(self.min_profit) / Decimal(100)
                    )

                    if low < self.market.limits_price_min:
                        low = self.market.limits_price_min

                    new_amount = order.amount * order.price
                    fee = new_amount * Decimal(0.001)

                    order.price = Decimal(low)
                    order.amount = new_amount - fee
                    order.side = Order.Side.SIDE_BUY
                    order.tick_counter = 0

        logger.info(order)

        total_quote_amount: Decimal
        if order.side == Order.Side.SIDE_BUY:
            total_quote_amount = order.amount
        else:
            total_quote_amount = order.amount * ticker_history[-1].closing_price

        # return of investment
        win: Decimal = total_quote_amount - quote_amount
        return (win / total_quote_amount * 100) - 100

    def __str__(self):
        return "{} | day_span {} | min_profit {}".format(
            self.market.symbol, self.day_span, self.min_profit
        )
