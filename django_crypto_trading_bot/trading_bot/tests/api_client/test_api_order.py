from datetime import datetime
from decimal import Decimal
from typing import List

import pytest
import pytz
from ccxt import Exchange

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
    get_or_create_market,
)
from django_crypto_trading_bot.trading_bot.api.order import (
    create_order,
    update_order_from_api_response,
)
from django_crypto_trading_bot.trading_bot.models import Bot, Market, Order, Trade
from django_crypto_trading_bot.trading_bot.tests.api_client.api_data_example import (
    order_structure,
)
from django_crypto_trading_bot.trading_bot.tests.factories import (
    AccountFactory,
    BotFactory,
    BtcCurrencyFactory,
    BuyOrderFactory,
    EthCurrencyFactory,
)


@pytest.mark.django_db()
def test_create_buy_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    bot = BotFactory()

    order: Order = create_order(
        amount=Decimal(1),
        price=Decimal(0.01),
        side="buy",
        bot=bot,
        isTestOrder=True,
        market=bot.market,
    )
    order2: Order = create_order(
        amount=Decimal(1),
        price=Decimal(0.01),
        side="buy",
        bot=bot,
        isTestOrder=True,
        market=bot.market,
    )

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "buy"
    assert len(Order.objects.all()) == 2


@pytest.mark.django_db()
def test_create_sell_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    bot = BotFactory()
    order: Order = create_order(
        amount=Decimal(1),
        price=Decimal(0.01),
        side="sell",
        bot=bot,
        isTestOrder=True,
        market=bot.market,
    )
    order2: Order = create_order(
        amount=Decimal(1),
        price=Decimal(0.01),
        side="sell",
        bot=bot,
        isTestOrder=True,
        market=bot.market,
    )

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "sell"
    assert len(Order.objects.all()) == 2


@pytest.mark.django_db()
def test_get_all_markets_from_exchange():
    # load all markets
    markets: List[Market] = get_all_markets_from_exchange(exchange_id="binance")

    # load markets from binance
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    # compare loaded markets with binance
    assert len(markets) == len(exchange.markets.values())


@pytest.mark.django_db()
def test_update_order_from_api_response():
    order: Order = BuyOrderFactory()

    order_dict: dict = order_structure(add_trades=True)

    order = update_order_from_api_response(cctx_order=order_dict, order=order)

    trade: Trade = Trade.objects.get(trade_id=order_dict["trades"][0]["id"])

    # assert trade
    assert trade.order == order
    assert trade.trade_id == order_dict["trades"][0]["id"]
    assert trade.timestamp == datetime.fromtimestamp(
        order_dict["trades"][0]["timestamp"] / 1000, tz=pytz.timezone("UTC")
    )
    assert trade.taker_or_maker == order_dict["trades"][0]["takerOrMaker"]
    assert trade.amount == Decimal(order_dict["trades"][0]["amount"])
    assert trade.fee_currency == EthCurrencyFactory()
    assert "{:.4f}".format(trade.fee_cost) == "{:.4f}".format(
        order_dict["trades"][0]["fee"]["cost"]
    )
    assert "{:.4f}".format(trade.fee_rate) == "{:.4f}".format(
        order_dict["trades"][0]["fee"]["rate"]
    )

    # assert order
    assert order.status == order_dict["status"]
    assert order.filled == order_dict["filled"]
    assert order.fee_currency == BtcCurrencyFactory()
    assert "{:.4f}".format(order.fee_cost) == "{:.4f}".format(order_dict["fee"]["cost"])
    assert "{:.4f}".format(order.fee_rate) == "{:.4f}".format(order_dict["fee"]["rate"])
