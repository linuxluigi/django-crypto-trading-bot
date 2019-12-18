import pytest
from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import (
    get_or_create_market,
    update_market,
    update_all_markets)
from .api_data_example import market_structure
from django_crypto_trading_bot.trading_bot.models import Market, Currency
from .factories import OutOfDataMarketFactory


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


@pytest.mark.django_db()
def test_update_market():
    # load outdated market
    out_of_data_market: Market = OutOfDataMarketFactory()

    # update market
    updated_market: Market = update_market(market=out_of_data_market)

    # get market from binance
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange: dict = exchange.market(out_of_data_market.symbol)

    assert isinstance(updated_market, Market)

    assert out_of_data_market.active != updated_market.active
    assert out_of_data_market.precision_amount != updated_market.precision_amount
    assert out_of_data_market.precision_price != updated_market.precision_price

    assert updated_market.active == market_exchange["active"]
    assert updated_market.precision_amount == market_exchange["precision"]["amount"]
    assert updated_market.precision_price == market_exchange["precision"]["price"]


@pytest.mark.django_db()
def test_update_all_markets():
    # load outdated market
    out_of_data_market: Market = OutOfDataMarketFactory()

    # update market
    updated_markets: list = update_all_markets()

    # get market from binance
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange: dict = exchange.market(out_of_data_market.symbol)

    for updated_market in updated_markets:
        assert isinstance(updated_market, Market)

        if updated_market.quote == out_of_data_market.quote and updated_market.base == out_of_data_market.base:
            assert out_of_data_market.active != updated_market.active
            assert out_of_data_market.precision_amount != updated_market.precision_amount
            assert out_of_data_market.precision_price != updated_market.precision_price

            assert updated_market.active == market_exchange["active"]
            assert updated_market.precision_amount == market_exchange["precision"]["amount"]
            assert updated_market.precision_price == market_exchange["precision"]["price"]
