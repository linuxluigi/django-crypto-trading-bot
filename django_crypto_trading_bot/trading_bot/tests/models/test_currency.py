import unittest

import pytest

from django_crypto_trading_bot.trading_bot.models import Currency

from ..factories import TrxCurrencyFactory


@pytest.mark.django_db()
class TestCurrency(unittest.TestCase):
    def test_to_string(self):
        trx: Currency = TrxCurrencyFactory()
        trx.pk = 1

        assert trx.__str__() == "1: TRX"
