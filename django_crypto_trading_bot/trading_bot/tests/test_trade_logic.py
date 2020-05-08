# import pytest
# from django_crypto_trading_bot.trading_bot.models import Order
# from django_crypto_trading_bot.trading_bot.trade_logic import TradeLogic
# from django_crypto_trading_bot.trading_bot.tests.factories import (
#     BuyOrderFactory,
#     SellOrderFactory,
# )
# from django_crypto_trading_bot.trading_bot.exceptions import (
#     InsufficientTradingAmount,
#     TickerWasNotSet,
# )
# from decimal import Decimal


# @pytest.mark.django_db()
# def test_min_profit_price(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):
#     # get price for new sell order
#     assert "{0:.3f}".format(trade_logic_buy.min_profit_price()) == "1.001"

#     # get price for new buy order
#     assert "{0:.3f}".format(trade_logic_sell.min_profit_price()) == "0.999"


# @pytest.mark.django_db()
# def test_trade_price(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):
#     # set high & low to use it instead of min profit
#     trade_logic_sell.ticker_low = 0.1
#     trade_logic_buy.ticker_high = 10

#     # check if high & low was triggert
#     assert trade_logic_sell.trade_price() == 0.1
#     assert trade_logic_buy.trade_price() == 10

#     # set high & low to use min profit
#     trade_logic_sell.low = 10
#     trade_logic_buy.high = 0.1

#     # assert if min profit was triggert
#     assert "{0:.3f}".format(trade_logic_buy.min_profit_price()) == "1.001"
#     assert "{0:.3f}".format(trade_logic_sell.min_profit_price()) == "0.999"


# @pytest.mark.django_db()
# def test_set_min_max_price(trade_logic_sell: TradeLogic):
#     # setup limits_price
#     trade_logic_sell.order.bot.market.limits_price_min = 1
#     trade_logic_sell.order.bot.market.limits_price_max = 10

#     assert trade_logic_sell.set_min_max_price(Decimal(11)) == 10
#     assert trade_logic_sell.set_min_max_price(Decimal(0)) == 1
#     assert trade_logic_sell.set_min_max_price(Decimal(5)) == 5


# @pytest.mark.django_db()
# def test_set_min_max_order_amount(trade_logic_sell: TradeLogic):
#     # setup limits_price
#     trade_logic_sell.order.bot.market.limits_amount_min = 1
#     trade_logic_sell.order.bot.market.limits_amount_max = 10

#     assert trade_logic_sell.set_min_max_order_amount(Decimal(11)) == 10
#     assert trade_logic_sell.set_min_max_order_amount(Decimal(0.5)) == 0
#     assert trade_logic_sell.set_min_max_order_amount(Decimal(5)) == 5


# @pytest.mark.django_db()
# def test_retrade_amount(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):
#     # get amount for new buy order
#     assert trade_logic_sell.retrade_amount(price=1) == 99.0
#     assert isinstance(trade_logic_sell.retrade_amount(price=10), Decimal)

#     # get amount for new buy order
#     assert trade_logic_buy.retrade_amount(price=10) == 100
#     assert isinstance(trade_logic_buy.retrade_amount(price=10), Decimal)


# @pytest.mark.django_db()
# def test_filter_amount(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):
#     assert isinstance(trade_logic_sell.filter_amount(amount=1), Decimal)
#     assert isinstance(trade_logic_buy.filter_amount(amount=1), Decimal)

#     # min amount 0.1 & max amount 1000
#     precision_amount: int = trade_logic_buy.order.bot.market.precision_amount

#     # new sell amount
#     assert trade_logic_buy.filter_amount(amount=Decimal(1)) == round(
#         Decimal(1), precision_amount
#     )
#     assert trade_logic_buy.filter_amount(amount=Decimal(0.01)) == round(
#         Decimal(0), precision_amount
#     )
#     assert trade_logic_buy.filter_amount(amount=Decimal(123.45678)) == round(
#         Decimal(123.4), precision_amount
#     )
#     assert trade_logic_buy.filter_amount(amount=Decimal(1.09)) == round(
#         Decimal(1), precision_amount
#     )
#     assert trade_logic_buy.filter_amount(amount=Decimal(1001)) == round(
#         Decimal(1000), precision_amount
#     )

#     # new buy price
#     assert trade_logic_sell.filter_amount(amount=Decimal(1)) == round(
#         Decimal(1), precision_amount
#     )
#     assert trade_logic_sell.filter_amount(amount=Decimal(0.01)) == round(
#         Decimal(0), precision_amount
#     )
#     assert trade_logic_sell.filter_amount(amount=Decimal(123.45678)) == round(
#         Decimal(123.4), precision_amount
#     )
#     assert trade_logic_sell.filter_amount(amount=Decimal(1.09)) == round(
#         Decimal(1), precision_amount
#     )
#     assert trade_logic_sell.filter_amount(amount=Decimal(1001)) == round(
#         Decimal(1000), precision_amount
#     )


# @pytest.mark.django_db()
# def test_filter_price(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):
#     assert isinstance(trade_logic_buy.filter_price(price=Decimal(1)), Decimal)
#     assert isinstance(trade_logic_sell.filter_price(price=Decimal(1)), Decimal)

#     # min price 0.1 & max price 1000
#     precision_price: int = trade_logic_buy.order.bot.market.precision_price

#     # new sell price
#     assert trade_logic_buy.filter_price(price=Decimal(1)) == round(
#         Decimal(1), precision_price
#     )
#     assert trade_logic_buy.filter_price(price=Decimal(0.01)) == round(
#         Decimal(0), precision_price
#     )
#     assert trade_logic_buy.filter_price(price=Decimal(123.45678)) == round(
#         Decimal(123.4), precision_price
#     )
#     assert trade_logic_buy.filter_price(price=Decimal(1.09)) == round(
#         Decimal(1), precision_price
#     )
#     assert trade_logic_buy.filter_price(price=Decimal(1001)) == round(
#         Decimal(1000), precision_price
#     )

#     # new buy price
#     assert trade_logic_sell.filter_price(price=Decimal(1)) == round(
#         Decimal(1), precision_price
#     )
#     assert trade_logic_sell.filter_price(price=Decimal(0.01)) == round(
#         Decimal(0), precision_price
#     )
#     assert trade_logic_sell.filter_price(price=Decimal(123.45678)) == round(
#         Decimal(123.4), precision_price
#     )
#     assert trade_logic_sell.filter_price(price=Decimal(1.09)) == round(
#         Decimal(1), precision_price
#     )
#     assert trade_logic_sell.filter_price(price=Decimal(1001)) == round(
#         Decimal(1000), precision_price
#     )


# @pytest.mark.django_db()
# def test_create_reorder(trade_logic_sell: TradeLogic, trade_logic_buy: TradeLogic):

#     # test with no ticker was set
#     with pytest.raises(TickerWasNotSet):
#         trade_logic_sell.create_reorder(simulation=True)

#     # set ticker
#     trade_logic_sell.ticker_high = Decimal(10)
#     trade_logic_sell.ticker_low = Decimal(10)
#     trade_logic_buy.ticker_high = Decimal(10)
#     trade_logic_sell.ticker_low = Decimal(10)

#     # create reorders
#     reoder_buy: Order = trade_logic_sell.create_reorder(simulation=True)
#     reoder_sell: Order = trade_logic_buy.create_reorder(simulation=True)

#     # check if reorder are valid
#     assert reoder_sell.side == Order.SIDE_SELL
#     assert reoder_sell.amount == Decimal(100)
#     assert reoder_buy.side == Order.SIDE_BUY
#     assert reoder_buy.amount == Decimal(110)

#     # test with insufficient trading amount
#     trade_logic_sell.order.filled = Decimal(0)
#     with pytest.raises(InsufficientTradingAmount):
#         trade_logic_sell.create_reorder(simulation=True)
