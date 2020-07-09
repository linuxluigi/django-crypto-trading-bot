import logging
from collections import OrderedDict
from decimal import ROUND_DOWN, Decimal, getcontext
from time import sleep
from typing import List, Optional

from ccxt.base.errors import (
    ExchangeNotAvailable,
    InsufficientFunds,
    InvalidOrder,
    RequestTimeout,
)

from .exceptions import (
    NoMarket,
    NoTimeFrame,
    BotHasNoStopLoss,
    OrderHasNoLastPrice,
    BotHasNoQuoteCurrency,
    BotHasNoMinRise,
)

from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.api.order import create_order
from django_crypto_trading_bot.trading_bot.models import (
    OHLCV,
    Bot,
    Currency,
    Market,
    Order,
    OrderErrorLog,
    Saving,
    Timeframes,
)

logger = logging.getLogger(__name__)


def run_wave_rider(candle: Optional[OHLCV] = None, test: bool = False):
    order: Order
    for order in Order.objects.filter(
        next_order=None,
        status=Order.Status.CLOSED,
        bot__trade_mode=Bot.TradeMode.WAVE_RIDER,
    ):
        # todo test add exeception
        if not order.bot.market:
            raise NoMarket("Bot has no market!")
        if not order.bot.timeframe:
            raise NoTimeFrame("Bot has no time frame!")

        if not candle:
            exchange: Exchange = order.bot.account.get_account_client()

            candles: List[List[float]]
            while True:
                try:
                    candles = exchange.fetch_ohlcv(
                        symbol=order.bot.market.symbol,
                        timeframe=order.bot.timeframe,
                        limit=1,
                    )
                    break
                except (RequestTimeout, ExchangeNotAvailable):
                    sleep(30)

            candle = OHLCV.get_OHLCV(
                candle=candles[0],
                timeframe=order.bot.timeframe,
                market=order.bot.market,
            )

        if candle:
            getcontext().prec = 8
            getcontext().rounding = ROUND_DOWN
            saving_amount: Decimal = Decimal(0)

            retrade_amount: Decimal
            if order.side == Order.Side.SIDE_BUY:
                retrade_amount = order.get_retrade_amount(price=candle.highest_price)
            else:
                retrade_amount = order.get_retrade_amount(price=candle.lowest_price)

            limits_amount_min: Decimal = order.bot.market.limits_amount_min
            if retrade_amount < limits_amount_min:
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

                        while True:
                            try:
                                order.next_order = create_order(
                                    amount=retrade_amount,
                                    price=candle.highest_price,
                                    side=Order.Side.SIDE_SELL,
                                    bot=order.bot,
                                    market=order.bot.market,
                                    isTestOrder=test,
                                )
                                break
                            except (RequestTimeout, ExchangeNotAvailable):
                                sleep(30)

                        saving_amount = (order.amount - retrade_amount) * order.price

                        if saving_amount:
                            Saving.objects.create(
                                order=order,
                                bot=order.bot,
                                amount=saving_amount,
                                currency=order.bot.market.quote,
                            )
                    else:
                        while True:
                            try:
                                order.next_order = create_order(
                                    amount=retrade_amount,
                                    price=candle.lowest_price,
                                    side=Order.Side.SIDE_BUY,
                                    bot=order.bot,
                                    market=order.bot.market,
                                    isTestOrder=test,
                                )
                                break
                            except (RequestTimeout, ExchangeNotAvailable):
                                sleep(30)

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


def run_rising_chart(test: bool = False):
    bot: Bot
    for bot in Bot.objects.filter(trade_mode=Bot.TradeMode.RISING_CHART, active=True):
        tickers: OrderedDict = bot.fetch_tickers()

        # todo test add exeception
        if not bot.stop_loss:
            raise BotHasNoStopLoss("Bot has no stop loss!")

        # sell or update orders
        order: Order
        for order in Order.objects.filter(
            bot=bot, side=Order.Side.SIDE_BUY, next_order=None, status=Order.Status.CLOSED,
        ):
            # todo test add exeception
            if not order.market:
                raise NoMarket("Order has no market!")
            if not order.last_price_tick:
                raise OrderHasNoLastPrice("Order has no last price tick!")

            last: Decimal = Decimal(tickers[order.market.symbol]["last"])
            change: Decimal = last - order.last_price_tick
            percentage: Decimal = change / order.last_price_tick * 100

            if percentage <= bot.stop_loss:
                # sell coins for stop loss
                while True:
                    # todo add exception for low balance
                    try:
                        order.next_order = create_order(
                            amount=order.amount,
                            side=Order.Side.SIDE_SELL,
                            bot=bot,
                            market=order.market,
                            price=tickers[order.market.symbol]["ask"],
                            isTestOrder=test,
                        )
                        order.save()
                        break
                    except (RequestTimeout, ExchangeNotAvailable):
                        sleep(30)
            else:
                # update order price
                order.last_price_tick = last
                order.save()

        ticker: dict
        for key, ticker in tickers.items():
            # jump to next ticker, if quote in market is not bot quote
            quote_str: str = ticker["symbol"].split("/")[1]

            # todo test add exeception
            quote: Currency
            if not bot.quote:
                BotHasNoQuoteCurrency("Bot has no quote currency!")
            else:
                if not bot.quote.short.upper() == quote_str.upper():
                    continue

            open_order_in_market: int = Order.objects.filter(
                bot=bot, side=Order.Side.SIDE_BUY, next_order=None
            ).count()

            # jump to next ticker, if bot is already active in market
            if open_order_in_market > 0:
                continue

            # todo test add exeception
            if bot.min_rise:
                # break if ticker percentage fall below bot min_rise
                if Decimal(ticker["percentage"]) < bot.min_rise:
                    break
            else:
                raise BotHasNoMinRise("Bot has no min rise!")

            base_str: str = ticker["symbol"].split("/")[0]
            base: Currency = Currency.objects.get(short=base_str.upper())
            market: Market = Market.objects.get(base=base, quote=bot.quote)

            quote_amount: Decimal = bot.fetch_balance(test=test)
            if bot.max_amount and quote_amount > bot.max_amount:
                quote_amount = bot.max_amount

            amount: Decimal = quote_amount / Decimal(ticker["bid"])

            amount = market.get_min_max_order_amount(amount=amount)
            if amount < market.limits_amount_min:
                break

            while True:
                try:
                    amount = market.get_min_max_order_amount(amount=amount)
                    if amount < market.limits_amount_min:
                        break

                    order = create_order(
                        amount=amount,
                        side=Order.Side.SIDE_BUY,
                        bot=bot,
                        market=market,
                        price=ticker["bid"],
                        isTestOrder=test,
                    )
                    order.market = market
                    order.last_price_tick = Decimal(ticker["bid"])
                    order.save()
                    break
                except (RequestTimeout, ExchangeNotAvailable):
                    sleep(30)
                except InsufficientFunds:
                    amount -= market.limits_amount_min * 5
