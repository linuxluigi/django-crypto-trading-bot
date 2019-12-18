from ccxt import Exchange
from django.utils.datetime_safe import datetime

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.models import Currency, Order


def create_buy_order(base: Currency, quote: Currency, amount, price, botId, isTestOrder):
    exchange: Exchange = get_client(exchange_id="binance")
    symbol = base.short + '/' + quote.short

    params = {
        'test': isTestOrder,  # test if it's valid, but don't actually place it
    }

    cctxOrder = exchange.create_order(symbol, 'limit', 'buy', amount, price, params)

    order: Order = None

    if isTestOrder:
        order: Order = Order(
            bot_id=botId,
            status="open",
            order_id=len(Order.objects.all()) + 1,
            order_type="limit",
            side="buy",
            timestamp=datetime.fromtimestamp(1545730073),
            price=price,
            amount=amount,
            filled=0,
            fee_currency=quote,
            fee_cost=0.0009,
            fee_rate=0.002
        )
    else:
        order = create_order_from_api_response(cctxOrder, botId)

    order.save()
    return order


def create_sell_order(base: Currency, quote: Currency, amount, price, botId, isTestOrder):
    exchange: Exchange = get_client(exchange_id="binance")
    symbol = base.short + '/' + quote.short

    params = {
        'test': isTestOrder,  # test if it's valid, but don't actually place it
    }

    cctxOrder = exchange.create_order(symbol, 'limit', 'sell', amount, price, params)

    order: Order = None

    if isTestOrder:
        order: Order = Order(
            bot_id=botId,
            status="open",
            order_id=len(Order.objects.all()) + 1,
            order_type="limit",
            side="sell",
            timestamp=datetime.fromtimestamp(1545730073),
            price=price,
            amount=amount,
            filled=0,
            fee_currency=quote,
            fee_cost=0.0009,
            fee_rate=0.002
        )
    else:
        order = create_order_from_api_response(cctxOrder, botId)

    order.save()
    return order


def create_order_from_api_response(cctxOrder, botId):
    return Order(
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
        fee_rate=cctxOrder["fee"]["rate"]
    )
