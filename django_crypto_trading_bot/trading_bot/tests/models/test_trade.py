import unittest
from decimal import Decimal

import pytest

from django_crypto_trading_bot.trading_bot.models import Trade

from ..factories import TradeFactory


@pytest.mark.django_db()
class TestCurrency(unittest.TestCase):
    def test_cost(self):
        trade: Trade = TradeFactory()

        assert trade.cost() == Decimal.from_float(1)
