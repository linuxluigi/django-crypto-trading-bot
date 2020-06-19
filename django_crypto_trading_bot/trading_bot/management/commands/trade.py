import logging
from typing import List

from ccxt.base.exchange import Exchange
from django.core.management.base import BaseCommand, CommandError

from django_crypto_trading_bot.trading_bot.api.order import (
    create_order,
    update_all_open_orders,
)
from django_crypto_trading_bot.trading_bot.models import OHLCV, Order, Timeframes, Trade

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update trades & create re orders."

    def handle(self, *args, **options):
        update_all_open_orders()

        order: Order
        for order in Order.objects.filter(next_order=None):
            exchange: Exchange = order.bot.account.get_account_client()

            candles: List[List[float]] = exchange.fetch_ohlcv(
                symbol=order.bot.market.symbol, timeframe=order.bot.timeframe, limit=1,
            )

            candle: OHLCV = OHLCV.get_OHLCV(
                candle=candles[0],
                timeframe=order.bot.timeframe,
                market=order.bot.market,
            )

            # todo add exceptions -> https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py

            if order.side == Order.Side.SIDE_BUY:
                order.next_order = create_order(
                    amount=order.get_retrade_amount(),
                    price=candle.highest_price,
                    side=Order.Side.SIDE_SELL,
                    bot=order.bot,
                )
            else:
                order.next_order = create_order(
                    amount=order.get_retrade_amount(),
                    price=candle.lowest_price,
                    side=Order.Side.SIDE_BUY,
                    bot=order.bot,
                )

            order.save()
            logger.info("create retrade {}".format(order.__str__()))
