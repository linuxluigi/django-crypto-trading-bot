from decimal import Decimal
from typing import List

from django.core.management.base import BaseCommand, CommandError

from django_crypto_trading_bot.trading_bot.api.order import create_order
from django_crypto_trading_bot.trading_bot.models import OHLCV, Bot, Order


class Command(BaseCommand):
    help = "Start the simulation"

    def add_arguments(self, parser):

        parser.add_argument(
            "--amount",
            nargs="?",
            type=int,
            help="Init Trade Amount",
            default=1,
        )

        parser.add_argument(
            "--bot_id",
            nargs="?",
            type=int,
            help="bot_id",
        )

    def handle(self, *args, **options):
        bot: Bot = Bot.objects.get(pk=options["bot_id"])

        exchange: Exchange = bot.account.get_account_client()

        candles: List[List[float]] = exchange.fetch_ohlcv(
            symbol=bot.market.symbol,
            timeframe=OHLCV.Timeframes.DAY_1,
            limit=1,
        )

        candle: OHLCV = OHLCV.get_OHLCV(
            candle=candles[0],
            timeframe=OHLCV.Timeframes.DAY_1,
            market=bot.market,
        )

        order: Order = create_order(
            amount=Decimal(options["amount"]),
            price=candle.lowest_price,
            side=Order.Side.SIDE_BUY,
            bot=bot,
        )
        order.save()
