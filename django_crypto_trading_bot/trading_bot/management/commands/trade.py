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

        trade: Trade
        for trade in Trade.objects.filter(re_order=None):
            exchange: Exchange = trade.order.bot.account.get_account_client()

            candles: List[List[float]] = exchange.fetch_ohlcv(
                symbol=trade.order.bot.market.symbol,
                timeframe=Timeframes.MONTH_1,
                limit=1,
            )

            candle: OHLCV = OHLCV.get_OHLCV(
                candle=candles[0],
                timeframe=Timeframes.MONTH_1,
                market=trade.order.bot.market,
            )

            # todo add exceptions -> https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py

            if trade.order.side == Order.Side.SIDE_BUY:
                trade.re_order = create_order(
                    amount=trade.get_retrade_amount(),
                    price=candle.highest_price,
                    side=Order.Side.SIDE_SELL,
                    bot=trade.order.bot,
                )
            else:
                trade.re_order = create_order(
                    amount=trade.get_retrade_amount(),
                    price=candle.lowest_price,
                    side=Order.Side.SIDE_BUY,
                    bot=trade.order.bot,
                )

            trade.save()
            logger.info("create retrade {}".format(trade.__str__()))
