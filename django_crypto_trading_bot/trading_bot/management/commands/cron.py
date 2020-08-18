import logging
import threading
import time
from datetime import datetime
from time import sleep

from crontab import CronTab
from django.core.management.base import BaseCommand

from django_crypto_trading_bot.trading_bot.api.market import (
    get_all_markets_from_exchange,
)
from django_crypto_trading_bot.trading_bot.api.order import update_all_open_orders
from django_crypto_trading_bot.trading_bot.trade import run_rising_chart, run_wave_rider

logger = logging.getLogger(__name__)


class Trade(threading.Thread):
    def run(self):
        ct: CronTab = CronTab("30 * * * * * *")

        while True:
            # get how long to wait for next cron
            now: datetime = datetime.utcnow()
            delay: float = ct.next(now, default_utc=True)

            sleep(delay)

            # run trade cron
            logger.info("Update all orders.")
            update_all_open_orders()
            logger.info("Run trading mode rising chart.")
            run_rising_chart()
            logger.info("Run trading mode wave rider.")
            run_wave_rider()


class UpdateMarket(threading.Thread):
    def run(self):
        ct: CronTab = CronTab("@hourly")

        while True:
            # get how long to wait for next cron
            now: datetime = datetime.utcnow()
            delay: float = ct.next(now, default_utc=True)

            sleep(delay)

            # run trade cron
            logger.info("update markets")
            get_all_markets_from_exchange("binance")


class Command(BaseCommand):
    help = "Run Cronjobs"

    def handle(self, *args, **options):

        trade_thread: Trade = Trade()
        update_market_thread: UpdateMarket = UpdateMarket()

        trade_thread.start()
        update_market_thread.start()

        trade_thread.join()
        update_market_thread.join()
