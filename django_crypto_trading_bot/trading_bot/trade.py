import logging
from decimal import ROUND_DOWN, Decimal, getcontext
from typing import List, Optional

from ccxt.base.errors import InsufficientFunds, InvalidOrder
from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.api.order import create_order
from django_crypto_trading_bot.trading_bot.models import (
    OHLCV,
    Order,
    OrderErrorLog,
    Saving,
    Timeframes,
)

logger = logging.getLogger(__name__)

def run_trade(candle: Optional[OHLCV] = None, test: bool = False):
    order: Order
    for order in Order.objects.filter(next_order=None, status=Order.Status.CLOSED):
        if not candle:
            exchange: Exchange = order.bot.account.get_account_client()

            candles: List[List[float]] = exchange.fetch_ohlcv(
                symbol=order.bot.market.symbol, timeframe=order.bot.timeframe, limit=1,
            )

            candle: OHLCV = OHLCV.get_OHLCV(
                candle=candles[0],
                timeframe=order.bot.timeframe,
                market=order.bot.market,
            )

        getcontext().prec = 8
        getcontext().rounding = ROUND_DOWN
        saving_amount: Decimal = Decimal(0)

        retrade_amount: Decimal
        if order.side == Order.Side.SIDE_BUY:
            retrade_amount = order.get_retrade_amount(price=candle.highest_price)
        else:
            retrade_amount = order.get_retrade_amount(price=candle.lowest_price)

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
            # todo add exceptions -> https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py
            try:
                if order.side == Order.Side.SIDE_BUY:

                    order.next_order = create_order(
                        amount=retrade_amount,
                        price=candle.highest_price,
                        side=Order.Side.SIDE_SELL,
                        bot=order.bot,
                        isTestOrder=test
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
                        isTestOrder=test,
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
            except InvalidOrder as e:
                logger.info(
                    "create retrade error for {} with {}".format(order.__str__(), e)
                )
                OrderErrorLog.objects.create(
                    order=order,
                    error_type=OrderErrorLog.ErrorTypes.InvalidOrder,
                    error_message=e,
                )
                continue

            order.save()
            logger.info("create retrade {}".format(order.__str__()))
