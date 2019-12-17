import pytest
from django_crypto_trading_bot.trading_bot.models import Account, Market
from .factories import AccountFactory, UserFactory, MarketFactory
from ccxt.base.exchange import Exchange


@pytest.mark.django_db()
def test_get_client():
    account: Account = AccountFactory()
    client: Exchange = account.get_client()

    balance: dict = client.fetch_balance()
    assert isinstance(balance, dict)


@pytest.mark.django_db()
def test_symbol():
    # check if symbol create the right symbol
    market: Market = MarketFactory()
    assert "TRX/BNB" == market.symbol

    # chekc if this symbol works on binance
    account: Account = AccountFactory()
    client: Exchange = account.get_client()
    client.load_markets()

    market_exchange = client.market(market.symbol)
    assert market.symbol == market_exchange["symbol"]
