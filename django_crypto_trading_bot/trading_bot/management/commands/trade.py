import logging

from django.core.management.base import BaseCommand

from django_crypto_trading_bot.trading_bot.api.order import update_all_open_orders
from django_crypto_trading_bot.trading_bot.trade import run_rising_chart, run_wave_rider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update trades & create re orders."

    def handle(self, *args, **options):
        logger.info("Update all orders.")
        update_all_open_orders()
        logger.info("Run trading mode rising chart.")
        run_rising_chart()
        logger.info("Run trading mode wave rider.")
        run_wave_rider()
