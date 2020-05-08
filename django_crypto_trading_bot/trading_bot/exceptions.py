class InsufficientTradingAmount(Exception):
    """
    Called when try to create a reader with insufficient trading amount
    """


class TickerWasNotSet(Exception):
    """
    Call when try to create a reorder without to set the ticker
    """


class SimulationMissCurrency(Exception):
    """
    Raise when a currency for the simulation is missing
    """


class SimulationMissMarket(Exception):
    """
    Raise when a market for the simulation is missing
    """
