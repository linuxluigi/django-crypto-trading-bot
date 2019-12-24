import pytest
from ccxt.base.exchange import Exchange
from django_crypto_trading_bot.trading_bot.api.client import get_client
from django_crypto_trading_bot.trading_bot.api.market import (
    get_or_create_market,
    update_market,
    update_all_markets,
)
from django_crypto_trading_bot.trading_bot.models import Market, Currency
from django_crypto_trading_bot.trading_bot.tests.factories import OutOfDataMarketFactory
from django_crypto_trading_bot.trading_bot.tests.api_client.api_data_example import (
    market_structure,
    market_structure_eth_btc,
)


@pytest.mark.django_db()
def test_get_or_create_market():
    default_market: dict = market_structure()

    # assert model
    market: Market = get_or_create_market(
        response=default_market, exchange_id="binance"
    )
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
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    # load outdated market
    out_of_data_market: Market = OutOfDataMarketFactory()

    # update market
    updated_market: Market = update_market(market=out_of_data_market, exchange=exchange)

    # get market from binance
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
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()

    out_of_data_market: Market = OutOfDataMarketFactory()
    get_or_create_market(response=market_structure_eth_btc(), exchange_id="binance")

    # update market
    update_all_markets(exchange)

    # get updatet market from the database
    updated_market: Market = Market.objects.get(pk=out_of_data_market.pk)

    # get market from binance
    market_exchange: dict = exchange.market(out_of_data_market.symbol)

    # assert if values changed
    assert out_of_data_market.active != updated_market.active
    assert out_of_data_market.precision_amount != updated_market.precision_amount
    assert out_of_data_market.precision_price != updated_market.precision_price

    # assert if value are set to market_exchange
    assert updated_market.active == market_exchange["active"]
    assert updated_market.precision_amount == market_exchange["precision"]["amount"]
    assert updated_market.precision_price == market_exchange["precision"]["price"]
