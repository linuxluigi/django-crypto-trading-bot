from django_crypto_trading_bot.trading_bot.models import Market, Currency
from django_crypto_trading_bot.trading_bot.api.client import get_client
from ccxt.base.exchange import Exchange


def get_or_create_market(response: dict) -> Market:
    """
    update or create a market based on the api json
    """
    base, create = Currency.objects.get_or_create(short=response["base"])
    quote, create = Currency.objects.get_or_create(short=response["quote"])

    try:
        market: Market = Market.objects.get(base=base, quote=quote)
        market.active = response["active"]
        market.precision_amount = response["precision"]["amount"]
        market.precision_price = response["precision"]["price"]
        market.limits_amount_min = response["limits"]["amount"]["min"]
        market.limits_amount_max = response["limits"]["amount"]["max"]
        market.limits_price_min = response["limits"]["price"]["min"]
        market.limits_price_max = response["limits"]["price"]["max"]
        market.save()
        return market

    except Market.DoesNotExist:
        market: Market = Market(
            base=base,
            quote=quote,
            active=response["active"],
            precision_amount=response["precision"]["amount"],
            precision_price=response["precision"]["price"],
            limits_amount_min=response["limits"]["amount"]["min"],
            limits_amount_max=response["limits"]["amount"]["max"],
            limits_price_min=response["limits"]["price"]["min"],
            limits_price_max=response["limits"]["price"]["max"]
        )
        market.save()
        return market


def update_market(market: Market) -> Market:
    """
    Update Market Order
    """
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    market_exchange: dict = exchange.market(market.symbol)
    return get_or_create_market(market_exchange)


def update_all_markets() -> list:
    """
    Update all markets
    :return: list with all updated market objects
    """
    updated_markets = list()
    exchange: Exchange = get_client(exchange_id="binance")
    exchange.load_markets()
    for market in Market.objects.all():
        updated_markets.append(get_or_create_market(exchange.market(market.symbol)))
    return updated_markets
