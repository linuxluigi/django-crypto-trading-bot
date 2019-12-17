from django_crypto_trading_bot.trading_bot.models import Market, Currency


def get_or_create_market(response: dict) -> Market:
    """
    update or create a market based on the api json
    """
    base, create = Currency.objects.get_or_create(short=response["base"])
    quote, create = Currency.objects.get_or_create(short=response["quote"])

    return Market(
        base=base,
        quote=quote,
        active=response["active"],
        precision_amount=response["precision"]["amount"],
        precision_price=response["precision"]["price"],
    )
