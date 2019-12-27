from __future__ import annotations
from ccxt import Exchange
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.models import Currency, Order, Bot, Market
import pytz


def create_order(
    amount: Decimal, price: Decimal, side: str, bot: Bot, isTestOrder: bool = False
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
            filled=0,
            fee_currency=bot.market.quote,
            fee_cost=0.0009,
            fee_rate=0.002,
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
    timezone.activate(pytz.timezone("UTC"))
    return Order.objects.create(
        bot=bot,
        status=cctx_order["status"],
        order_id=cctx_order["id"],
        order_type=cctx_order["type"],
        side=cctx_order["side"],
        timestamp=datetime.fromtimestamp(cctx_order["timestamp"]),
        price=cctx_order["price"],
        amount=cctx_order["amount"],
        filled=cctx_order["filled"],
        fee_currency=Currency(short=cctx_order["fee"]["currency"]),
        fee_cost=cctx_order["fee"]["cost"],
        fee_rate=cctx_order["fee"]["rate"],
    )


def update_order_from_api_response(cctx_order: dict, order: Order) -> Order:
    """
    Parse API response to update a order object
    """
    if order.status != cctx_order["status"]:
        # todo trigger event when status changed
        pass
    order.status = cctx_order["status"]
    order.filled = cctx_order["filled"]
    order.fee_cost = cctx_order["fee"]["cost"]
    order.fee_rate = cctx_order["fee"]["rate"]
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
    for order in Order.objects.filter(status=Order.status_choice["open"]):
        get_order_from_exchange(order=order)
