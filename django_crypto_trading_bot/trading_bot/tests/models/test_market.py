import unittest
from decimal import Decimal, getcontext

import pytest
from ccxt.base.exchange import Exchange

from django_crypto_trading_bot.trading_bot.models import Account, Market
from django_crypto_trading_bot.trading_bot.models.choices import ExchangesOptions

from ..factories import AccountFactory, EthBtcMarketFactory, MarketFactory


@pytest.mark.django_db()
class TestMarket(unittest.TestCase):
    def test_to_string(self):
        """
        test __str__
        """
        market: Market = MarketFactory()
        assert market.__str__() == "TRX/BNB"

    def test_symbol(self):
        """
        test symbol
        """
        # check if symbol create the right symbol
        market: Market = MarketFactory()
        assert market.symbol == "TRX/BNB"

        # check if this symbol works on binance
        account: Account = AccountFactory()
        client: Exchange = account.get_account_client()
        client.load_markets()

        market_exchange = client.market(market.symbol)
        assert market.symbol == market_exchange["symbol"]

    def test_market_id(self):
        """
        test market_id
        """
        market: Market = MarketFactory()
        assert market.market_id == "trxbnb"

    def test_baseId(self):
        """
        test baseId
        """
        market: Market = MarketFactory()
        assert market.baseId == "trx"

    def test_quoteId(self):
        """
        test quoteId
        """
        market: Market = MarketFactory()
        assert market.quoteId == "bnb"

    def test_get_min_max_price(self):
        """
        test get_min_max_price
        """
        market: Market = MarketFactory()
        getcontext().prec = market.precision_amount

        # test minimum
        assert "{:.3f}".format(
            market.get_min_max_price(market.limits_price_min / 2)
        ) == "{:.3f}".format(0.100)
        # test maximum
        assert "{:.3f}".format(
            market.get_min_max_price(market.limits_price_max * 2)
        ) == "{:.3f}".format(market.limits_price_max)
        # test valid price
        assert "{:.3f}".format(
            market.get_min_max_price(Decimal(10.3))
        ) == "{:.3f}".format(10.3)
        # test precision_price 0
        market.precision_price = 0
        assert "{:.3f}".format(
            market.get_min_max_price(Decimal(10.321))
        ) == "{:.3f}".format(10.321)

    def test_get_min_max_order_amount(self):
        """
        test get_min_max_order_amount
        """
        market: Market = MarketFactory()
        getcontext().prec = market.precision_amount

        # test minimum
        assert "{:.3f}".format(
            market.get_min_max_order_amount(market.limits_amount_min / 2)
        ) == "{:.3f}".format(0)
        # test maximum
        assert "{:.3f}".format(
            market.get_min_max_order_amount(market.limits_amount_max * 2)
        ) == "{:.3f}".format(market.limits_amount_max)
        # test valid amount
        assert "{:.3f}".format(
            market.get_min_max_order_amount(Decimal(10.3))
        ) == "{:.3f}".format(10.3)
        # test precision_amount 0
        market.precision_amount = 0
        assert "{:.3f}".format(
            market.get_min_max_order_amount(Decimal(10.321))
        ) == "{:.3f}".format(10)

    def test_get_market(self):
        """
        test get_market
        """
        # create a market in the database
        market_original: Market = EthBtcMarketFactory()

        # get the market by symbol & exchange
        market_get: Market = Market.get_market(
            symbol=market_original.symbol,
            exchange=ExchangesOptions(market_original.exchange),
        )

        # check if the right market was get from the database
        assert market_get.pk == market_original.pk
