import pytest
from ccxt import Exchange

from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import get_or_create_market
from django_crypto_trading_bot.trading_bot.api.order import create_order
from django_crypto_trading_bot.trading_bot.models import Order, Market
from django_crypto_trading_bot.trading_bot.tests.factories import BotFactory


@pytest.mark.django_db()
def test_create_buy_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    btc_eth_market: Market = get_or_create_market(response=exchange.market('ETH/BTC'))
    bot = BotFactory()
    order: Order = create_order(btc_eth_market.base, btc_eth_market.quote, 1, 0.01, 'buy', botId=bot.id,
                                isTestOrder=True)
    order2: Order = create_order(btc_eth_market.base, btc_eth_market.quote, 1, 0.01, 'buy', botId=bot.id,
                                 isTestOrder=True)

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "buy"
    assert len(Order.objects.all()) == 2


@pytest.mark.django_db()
def test_create_sell_order():
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    btc_eth_market: Market = get_or_create_market(response=exchange.market('ETH/BTC'))
    bot = BotFactory()
    order: Order = create_order(btc_eth_market.base, btc_eth_market.quote, 1, 0.01, 'sell', botId=bot.id,
                                isTestOrder=True)
    order2: Order = create_order(btc_eth_market.base, btc_eth_market.quote, 1, 0.01, 'sell', botId=bot.id,
                                 isTestOrder=True)

    assert isinstance(order, Order)
    assert isinstance(order2, Order)
    assert order.side == "sell"
    assert len(Order.objects.all()) == 2
