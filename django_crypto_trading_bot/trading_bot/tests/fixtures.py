def trade_dict(trade_id: str = "12345-67890:09876/54321") -> dict:
    """
    Create a trade response dict

    -> https://github.com/ccxt/ccxt/wiki/Manual#trade-structure

    Args:
        trade_id (str, optional): trade id. Defaults to "12345-67890:09876/54321".

    Returns:
        dict: trade response dict
    """
    return {
        "id": trade_id,  # string trade id
        "timestamp": 1502962946216,  # Unix timestamp in milliseconds
        "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime with milliseconds
        "symbol": "ETH/BTC",  # symbol
        "order": "12345-67890:09876/54321",  # string order id or undefined/None/null
        "type": "limit",  # order type, 'market', 'limit' or undefined/None/null
        "side": "buy",  # direction of the trade, 'buy' or 'sell'
        "takerOrMaker": "taker",  # string, 'taker' or 'maker'
        "price": 0.06917684,  # float price in quote currency
        "amount": 1.5,  # amount of base currency
        "cost": 0.10376526,  # total cost, `price * amount`,
        "fee": {  # provided by exchange or calculated by ccxt
            "cost": 0.0015,  # float
            "currency": "ETH",  # usually base currency for buys, quote currency for sells
            "rate": 0.002,  # the fee rate (if available)
        },
    }


def order_dict(order_id: str = "12345-67890:09876/54321") -> dict:
    """
    Create a order response dict

    -> https://github.com/ccxt/ccxt/wiki/Manual#order-structure

    Args:
        order_id (str, optional): order id. Defaults to "12345-67890:09876/54321".

    Returns:
        dict: order response dict
    """
    return {
        "id": order_id,  # string
        "clientOrderId": "abcdef-ghijklmnop-qrstuvwxyz",  # a user-defined clientOrderId, if any
        "datetime": "2017-08-17 12:42:48.000",  # ISO8601 datetime of 'timestamp' with milliseconds
        "timestamp": 1502962946216,  # order placing/opening Unix timestamp in milliseconds
        "lastTradeTimestamp": 1502962956216,  # Unix timestamp of the most recent trade on this order
        "status": "open",  # 'open', 'closed', 'canceled', 'expired'
        "symbol": "ETH/BTC",  # symbol
        "type": "limit",  # 'market', 'limit'
        "timeInForce": "GTC",  # 'GTC', 'IOC', 'FOK', 'PO'
        "side": "buy",  # 'buy', 'sell'
        "price": 0.06917684,  # float price in quote currency (may be empty for market orders)
        "average": 0.06917684,  # float average filling price
        "amount": 1.5,  # ordered amount of base currency
        "filled": 1.1,  # filled amount of base currency
        "remaining": 0.4,  # remaining amount to fill
        "cost": 0.076094524,  # 'filled' * 'price' (filling price used where available)
        "trades": [
            trade_dict(trade_id=1),
            trade_dict(trade_id=2),
        ],  # a list of order trades/executions
        "fee": {  # fee info, if available
            "currency": "BTC",  # which currency the fee is (usually quote)
            "cost": 0.0009,  # the fee amount in that currency
            "rate": 0.002,  # the fee rate (if available)
        },
    }
