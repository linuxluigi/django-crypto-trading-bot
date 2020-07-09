from django.core.management.base import BaseCommand

from django_crypto_trading_bot.trading_bot.models import OHLCV, Timeframes


class Command(BaseCommand):
    help = "Download the chart history of all markets for a timeframe"

    def add_arguments(self, parser):

        parser.add_argument(
            "--timeframe",
            nargs="?",
            type=Timeframes,
            help="Timeframe like 1m, 1h, 1d, 1w, 1M, ...",
            default=Timeframes.DAY_1,
        )

    def handle(self, *args, **options):
        OHLCV.update_new_candles_all_markets(timeframe=options["timeframe"])
