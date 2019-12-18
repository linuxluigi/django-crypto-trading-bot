# example objects from https://github.com/ccxt/ccxt/wiki/Manual


def trade_structure() -> dict:
    return {
        "id": "12345-67890:09876/54321",
        "timestamp": 1502962946216,
        "datetime": "2017-08-17 12:42:48.000",
        "symbol": "ETH/BTC",
        "order": "12345-67890:09876/54321",
        "type": "limit",
        "side": "buy",
        "takerOrMaker": "taker",
        "price": 0.06917684,
        "amount": 1.5,
        "cost": 0.10376526,
        "fee": {"cost": 0.0015, "currency": "ETH", "rate": 0.002},
    }


def order_structure(add_trades: bool) -> dict:
    """
    get dummy order

    add_trades -> add a trade to order
    """
    order_structure: dict = {
        "id": "12345-67890:09876/54321",
        "datetime": "2017-08-17 12:42:48.000",
        "timestamp": 1502962946216,
        "lastTradeTimestamp": 1502962956216,
        "status": "open",
        "symbol": "ETH/BTC",
        "type": "limit",
        "side": "buy",
        "price": 0.06917684,
        "amount": 1.5,
        "filled": 1.1,
        "remaining": 0.4,
        "cost": 0.076094524,
        "trades": [],
        "fee": {"currency": "BTC", "cost": 0.0009, "rate": 0.002},
    }

    if add_trades:
        order_structure["trades"] = [trade_structure()]

    return order_structure


def market_structure() -> dict:
    return {
        "id": " btcusd",
        "symbol": "BTC/USDT",
        "base": "BTC",
        "quote": "USDT",
        "baseId": "btc",
        "quoteId": "usdt",
        "active": True,
        "precision": {"price": 8, "amount": 8, "cost": 8},
        "limits": {"amount": {"min": 0.01, "max": 1000}, "price": {"min": 0.01, "max": 1000000.0}},
    }


def market_structure_eth_btc() -> dict:
    return {
        "id": " ETHBTC",
        "symbol": "ETH/BTC",
        "base": "ETH",
        "quote": "BTC",
        "baseId": "ETH",
        "quoteId": "BTC",
        "active": True,
        "precision": {"price": 8, "amount": 3, "cost": 3},
        "limits": {"amount": {"min": 0.001, "max": 100000}, "price": {"min": 1e-06, "max": 100000.0}},
    }
