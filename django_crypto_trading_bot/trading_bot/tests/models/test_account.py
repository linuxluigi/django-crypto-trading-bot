import unittest

import pytest
from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.models import Account

from ..factories import AccountFactory


@pytest.mark.django_db()
class TestAccount(unittest.TestCase):
    def test_get_account_client(self):
        """
        test get_account_client
        """
        account: Account = AccountFactory()
        client: Exchange = account.get_account_client()

        assert isinstance(client, Exchange)

    def test_to_string(self):
        """
        test __str__
        """
        account: Account = AccountFactory()

        assert (
            account.__str__()
            == f"{account.pk}: binance - {account.user.get_username()}"
        )
