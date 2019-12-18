from ccxt.base.exchange import Exchange
import ccxt
import os


def get_client(exchange_id: str, api_key: str = None, secret: str = None) -> Exchange:
    if exchange_id == "binance":
        api_key = os.environ['BINANCE_SANDBOX_API_KEY']
        secret = os.environ['BINANCE_SANDBOX_SECRET_KEY']
    exchange_class = getattr(ccxt, exchange_id)
    exchange: Exchange = exchange_class(
        {"apiKey": api_key, "secret": secret, "timeout": 30000, "enableRateLimit": True}
    )

    return exchange
