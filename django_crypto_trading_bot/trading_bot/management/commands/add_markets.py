from django.core.management.base import BaseCommand, CommandError
from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
)


class Command(BaseCommand):
    help = "Add & update all markets from exchange in db"

    def add_arguments(self, parser):
        parser.add_argument(
            "exchange",
            nargs="?",
            type=str,
            help="Exchange like binance",
            default="binance",
        )

    def handle(self, *args, **options):

        # todo check if exchange exists
        exchange: str = options["exchange"].lower()

        # add & update all markets from exchange in db
        get_all_markets_from_exchange(exchange)

        print("All markets for {} added & updated in the database!".format(exchange))
