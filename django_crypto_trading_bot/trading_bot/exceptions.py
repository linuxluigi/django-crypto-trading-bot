class InsufficientTradingAmount(Exception):
    """
    Called when try to create a reader with insufficient trading amount
    """


class TickerWasNotSet(Exception):
    """
    Call when try to create a reorder without to set the ticker
    """


class PriceToLow(Exception):
    """
    Call when try use a price below minimum amount
    """


class PriceToHigh(Exception):
    """
    Call when try use a price above maximum amount
    """


class FunktionNotForTradeMode(Exception):
    """
    Funktion is not implemented for trade mode
    """


class NoQuoteCurrency(Exception):
    """
    Bot has not quote currency
    """


class NoMarket(Exception):
    """
    Bot & order has no market!
    """


class NoTimeFrame(Exception):
    """
    Bot has no Timeframe!
    """


class BotHasNoStopLoss(Exception):
    """
    Bot has no stop loss!
    """


class BotHasNoQuoteCurrency(Exception):
    """
    Bot has no quote currency!
    """


class BotHasNoMinRise(Exception):
    """
    Bot has no min rise!
    """


class OrderHasNoLastPrice(Exception):
    """
    Order has no last price tick!
    """
