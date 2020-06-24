import logging
from decimal import ROUND_DOWN, Decimal, getcontext
from typing import List

from ccxt.base.errors import InsufficientFunds
from ccxt.base.exchange import Exchange
from django.core.management.base import BaseCommand, CommandError

from django_crypto_trading_bot.trading_bot.api.order import (
    create_order,
    update_all_open_orders,
)
from django_crypto_trading_bot.trading_bot.models import (
    OHLCV,
    Order,
    OrderErrorLog,
    Saving,
    Timeframes,
    Trade,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update trades & create re orders."

    def handle(self, *args, **options):
        update_all_open_orders()

        order: Order
        for order in Order.objects.filter(next_order=None, status=Order.Status.CLOSED):
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

            try:
                getcontext().prec = 8
                getcontext().rounding = ROUND_DOWN
                saving_amount: Decimal = Decimal(0)
                retrade_amount: Decimal = order.get_retrade_amount()

                if retrade_amount < order.bot.market.limits_amount_min:
                    if order.side == Order.Side.SIDE_BUY:
                        Saving.objects.create(
                            order=order,
                            bot=order.bot,
                            amount=order.amount * order.price,
                            currency=order.bot.market.quote,
                        )
                    else:
                        Saving.objects.create(
                            order=order,
                            bot=order.bot,
                            amount=order.amount,
                            currency=order.bot.market.base,
                        )

                    order.bot.active = False
                    order.status = Order.Status.NOT_MIN_NOTIONAL
                    order.bot.save()
                    order.save()

                else:
                    if order.side == Order.Side.SIDE_BUY:

                        order.next_order = create_order(
                            amount=retrade_amount,
                            price=candle.highest_price,
                            side=Order.Side.SIDE_SELL,
                            bot=order.bot,
                        )

                        saving_amount = (order.amount - retrade_amount) * order.price

                        if saving_amount:
                            Saving.objects.create(
                                order=order,
                                bot=order.bot,
                                amount=saving_amount,
                                currency=order.bot.market.quote,
                            )

                    else:
                        order.next_order = create_order(
                            amount=retrade_amount,
                            price=candle.lowest_price,
                            side=Order.Side.SIDE_BUY,
                            bot=order.bot,
                        )

                        saving_amount = order.amount - retrade_amount

                        if saving_amount:
                            Saving.objects.create(
                                order=order,
                                bot=order.bot,
                                amount=saving_amount,
                                currency=order.bot.market.base,
                            )

            except InsufficientFunds as e:
                logger.info(
                    "create retrade error for {} with {}".format(order.__str__(), e)
                )
                OrderErrorLog.objects.create(
                    order=order,
                    error_type=OrderErrorLog.ErrorTypes.Insufficient_Funds,
                    error_message=e,
                )
                continue

            order.save()
            logger.info("create retrade {}".format(order.__str__()))
