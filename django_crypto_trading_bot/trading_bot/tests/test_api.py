import pytest
from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import get_or_create_market
from .api_data_example import market_structure
from django_crypto_trading_bot.trading_bot.models import Market, Currency


def test_get_client():
    # check if puplic api works
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange = exchange.market("TRX/BNB")
    assert "TRX/BNB" == market_exchange["symbol"]


@pytest.mark.django_db()
def test_get_or_create_market():
    default_market: dict = market_structure()

    # assert model
    market: Market = get_or_create_market(response=default_market)
    assert isinstance(market, Market)
    assert market.active == default_market["active"]
    assert isinstance(market.base, Currency)
    assert isinstance(market.quote, Currency)
    assert market.precision_amount == default_market["precision"]["amount"]
    assert market.precision_price == default_market["precision"]["price"]

    # test if new market works on binance
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange = exchange.market(default_market["symbol"])
    assert default_market["symbol"] == market_exchange["symbol"]
