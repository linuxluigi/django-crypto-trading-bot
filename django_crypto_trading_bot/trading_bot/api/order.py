from ccxt import Exchange
from django.utils.datetime_safe import datetime

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.models import Currency, Order


def create_order(
    base: Currency, quote: Currency, amount, price, side, botId, isTestOrder
):
    """
    Create an order
    :param base: base currency
    :param quote: destination currency
    :param amount: amount you want to buy
    :param price: the price you want to spend
    :param side: sell or buy order?
    :param botId: id of the bot which has placed the order
    :param isTestOrder: is this a test order?
    :return: Order object
    """
    exchange: Exchange = get_client(exchange_id="binance")
    symbol = base.short + "/" + quote.short

    params = {"test": isTestOrder}  # test if it's valid, but don't actually place it

    cctxOrder = exchange.create_order(symbol, "limit", side, amount, price, params)

    if isTestOrder:
        return Order.objects.create(
            bot_id=botId,
            status="open",
            order_id=len(Order.objects.all()) + 1,
            order_type="limit",
            side=side,
            timestamp=datetime.fromtimestamp(1545730073),
            price=price,
            amount=amount,
            filled=0,
            fee_currency=quote,
            fee_cost=0.0009,
            fee_rate=0.002,
        )
    else:
        return __create_order_from_api_response(cctxOrder, botId)


def __create_order_from_api_response(cctxOrder, botId):
    """
    Parse response api response into object
    :param cctxOrder: the api response object
    :param botId: the id of the bot which has fired the request
    :return: Order object
    """
    return Order.objects.create(
        bot_id=botId,
        status=cctxOrder["status"],
        order_id=cctxOrder["id"],
        order_type=cctxOrder["type"],
        side=cctxOrder["side"],
        timestamp=cctxOrder["timestamp"],
        price=cctxOrder["price"],
        amount=cctxOrder["amount"],
        filled=cctxOrder["filled"],
        fee_currency=Currency(short=cctxOrder["fee"]["currency"]),
        fee_cost=cctxOrder["fee"]["cost"],
        fee_rate=cctxOrder["fee"]["rate"],
    )
