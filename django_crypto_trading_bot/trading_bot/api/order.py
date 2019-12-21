from ccxt import Exchange
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.models import Currency, Order, Bot, Market
import pytz


def create_order(
    amount: Decimal, price: Decimal, side: str, bot: Bot, isTestOrder: bool = False
):
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
        cctxOrder: dict = exchange.create_order(
            bot.market.symbol, "limit", side, amount, price, params
        )

        return create_order_from_api_response(cctxOrder, bot)


def create_order_from_api_response(cctxOrder: dict, bot: Bot):
    """
    Parse response api response into object
    :param cctxOrder: the api response object
    :param botId: the id of the bot which has fired the request
    :return: Order object
    """
    timezone.activate(pytz.timezone("UTC"))
    return Order.objects.create(
        bot=bot,
        status=cctxOrder["status"],
        order_id=cctxOrder["id"],
        order_type=cctxOrder["type"],
        side=cctxOrder["side"],
        timestamp=datetime.fromtimestamp(cctxOrder["timestamp"]),
        price=cctxOrder["price"],
        amount=cctxOrder["amount"],
        filled=cctxOrder["filled"],
        fee_currency=Currency(short=cctxOrder["fee"]["currency"]),
        fee_cost=cctxOrder["fee"]["cost"],
        fee_rate=cctxOrder["fee"]["rate"],
    )
