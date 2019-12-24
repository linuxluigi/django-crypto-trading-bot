import pytest
from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.client import get_client


def test_get_client():
    # check if puplic api works
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange = exchange.market("TRX/BNB")
    assert market_exchange["symbol"] == "TRX/BNB"
