from django.core.management.base import BaseCommand, CommandError
from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation


class Command(BaseCommand):
    help = "Start the simulation"

    def handle(self, *args, **options):
        simulation: Simulation = Simulation(
            day_span=[1, 2, 3, 5, 10, 15, 20, 30, 60],
            min_profit=[0.2, 0.5, 1, 2, 3, 5, 10],
            history_days=365,
        )
        simulation.run_simulation()
