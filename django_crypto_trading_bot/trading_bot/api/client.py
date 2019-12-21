from ccxt.base.exchange import Exchange
import ccxt
import os


def get_client(exchange_id: str, api_key: str = None, secret: str = None) -> Exchange:
    developmentMode = (
        os.environ.get("DJANGO_DEVELOPMENT") is not None
        and os.environ["DJANGO_DEVELOPMENT"] == "true"
    )
    if exchange_id == "binance" and developmentMode:
        api_key = os.environ["BINANCE_SANDBOX_API_KEY"]
        secret = os.environ["BINANCE_SANDBOX_SECRET_KEY"]
    exchange_class = getattr(ccxt, exchange_id)
    exchange: Exchange = exchange_class(
        {"apiKey": api_key, "secret": secret, "timeout": 30000, "enableRateLimit": True}
    )

    return exchange
