import pytest
from django_crypto_trading_bot.trading_bot.models import Account
from .factories import AccountFactory, UserFactory
from ccxt.base.exchange import Exchange


@pytest.mark.django_db()
def test_get_client():
    account: Account = AccountFactory()
    client: Exchange = account.get_client()

    balance: dict = client.fetch_balance()
    assert isinstance(balance, dict)
