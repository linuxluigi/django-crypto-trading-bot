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
