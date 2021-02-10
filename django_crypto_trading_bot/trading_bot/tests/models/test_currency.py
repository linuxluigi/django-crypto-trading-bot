import unittest

import pytest

from django_crypto_trading_bot.trading_bot.models import currency

from ..factories import TrxCurrencyFactory


@pytest.mark.django_db()
class TestCurrency(unittest.TestCase):
    def test_to_string(self):
        trx: currency = TrxCurrencyFactory()

        trx.pk = 1
        trx.order_id = "12"

        assert trx.__str__() == "1: TRX"
