import unittest

import pytest
from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.models import Account

from ..factories import AccountFactory


@pytest.mark.django_db()
class TestAccount(unittest.TestCase):
    def test_get_account_client(self):
        account: Account = AccountFactory()
        client: Exchange = account.get_account_client()

        assert isinstance(client, Exchange)
