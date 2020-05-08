class InsufficientTradingAmount(Exception):
    """
    Called when try to create a reader with insufficient trading amount
    """


class TickerWasNotSet(Exception):
    """
    Call when try to create a reorder without to set the ticker
    """
