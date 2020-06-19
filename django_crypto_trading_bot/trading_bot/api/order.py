from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytz
from ccxt import Exchange
from django.utils import timezone

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.models import (
    Bot,
    Currency,
    Market,
    Order,
    Trade,
)


def create_order(
    amount: Decimal,
    price: Decimal,
    side: Order.Side,
    bot: Bot,
    isTestOrder: bool = False,
) -> Order:
    """
    Create an order
    :param amount: amount you want to buy
    :param price: the price you want to spend
    :param side: sell or buy order?
    :param botId: id of the bot which has placed the order
    :param isTestOrder: is this a test order?
    :return: Order object
    """
    exchange: Exchange = bot.account.get_account_client()

    params = {"test": isTestOrder}  # test if it's valid, but don't actually place it

    if isTestOrder:

        return Order.objects.create(
            bot=bot,
            status="open",
            order_id=len(Order.objects.all()) + 1,
            order_type="limit",
            side=side,
            timestamp=timezone.now(),
            price=price,
            amount=amount,
            filled=Decimal(0),
        )
    else:
        cctx_order: dict = exchange.create_order(
            bot.market.symbol, "limit", side, amount, price, params
        )

        return create_order_from_api_response(cctx_order, bot)


def create_order_from_api_response(cctx_order: dict, bot: Bot) -> Order:
    """
    Parse response api response into object
    :param cctx_order: the api response object
    :param botId: the id of the bot which has fired the request
    :return: Order object
    """
    side: Order.Side
    if cctx_order["side"] == "buy":
        side = Order.Side.SIDE_BUY
    else:
        side = Order.Side.SIDE_SELL

    return Order.objects.create(
        bot=bot,
        status=cctx_order["status"],
        order_id=cctx_order["id"],
        order_type=cctx_order["type"],
        side=side,
        timestamp=datetime.fromtimestamp(
            cctx_order["timestamp"] / 1000, tz=pytz.timezone("UTC")
        ),
        price=Decimal(cctx_order["price"]),
        amount=Decimal(cctx_order["amount"]),
        filled=Decimal(cctx_order["filled"]),
    )


def update_order_from_api_response(cctx_order: dict, order: Order) -> Order:
    """
    Parse API response to update a order object
    """
    order.status = cctx_order["status"]
    order.filled = Decimal(cctx_order["filled"])

    if "fee" in cctx_order:
        if cctx_order["fee"]:
            currency, c_created = Currency.objects.get_or_create(
                short=cctx_order["fee"]["currency"],
            )
            order.fee_currency = currency
            order.fee_cost = Decimal(cctx_order["fee"]["cost"])
            order.fee_rate = Decimal(cctx_order["fee"]["rate"])

    if order.filled:
        if cctx_order["trades"]:
            for order_trade in cctx_order["trades"]:
                currency, c_created = Currency.objects.get_or_create(
                    short=order_trade["fee"]["currency"],
                )

                trade, created = Trade.objects.get_or_create(
                    order=order,
                    trade_id=order_trade["id"],
                    timestamp=datetime.fromtimestamp(
                        order_trade["timestamp"] / 1000, tz=pytz.timezone("UTC")
                    ),
                    taker_or_maker=order_trade["takerOrMaker"],
                    amount=Decimal(order_trade["amount"]),
                    fee_currency=currency,
                    fee_cost=Decimal(order_trade["fee"]["cost"]),
                    fee_rate=Decimal(order_trade["fee"]["rate"]),
                )

    order.save()
    return order


def get_order_from_exchange(order: Order):
    """
    get order from api repsonse & update the order model
    """
    exchange: Exchange = order.bot.account.get_account_client()
    cctx_order: dict = exchange.fetch_order(
        id=order.order_id, symbol=order.bot.market.symbol
    )
    return update_order_from_api_response(cctx_order=cctx_order, order=order)


def update_all_open_orders():
    """
    update all open orders
    """
    for order in Order.objects.filter(status=Order.Status.OPEN):
        get_order_from_exchange(order=order)
