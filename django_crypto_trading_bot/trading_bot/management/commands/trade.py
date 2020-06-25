from django.core.management.base import BaseCommand, CommandError

from django_crypto_trading_bot.trading_bot.api.order import update_all_open_orders
from django_crypto_trading_bot.trading_bot.trade import run_trade


class Command(BaseCommand):
    help = "Update trades & create re orders."

    def handle(self, *args, **options):
        update_all_open_orders()
        run_trade()
