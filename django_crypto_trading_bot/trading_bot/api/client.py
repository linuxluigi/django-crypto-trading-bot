from ccxt.base.exchange import Exchange
import ccxt


def get_client(exchange_id: str, api_key: str = None, secret: str = None) -> Exchange:
    exchange_class = getattr(ccxt, exchange_id)
    exchange: Exchange = exchange_class(
        {"apiKey": api_key, "secret": secret, "timeout": 30000, "enableRateLimit": True}
    )

    return exchange
