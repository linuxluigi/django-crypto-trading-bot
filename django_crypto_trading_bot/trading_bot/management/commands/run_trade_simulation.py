from django.core.management.base import BaseCommand, CommandError

from django_crypto_trading_bot.trading_bot.simulation.simulation import Simulation


class Command(BaseCommand):
    help = "Start the simulation"

    def add_arguments(self, parser):

        parser.add_argument(
            "--threads",
            nargs="?",
            type=int,
            help="How many simulations should run at once",
            default=1,
        )

    def handle(self, *args, **options):
        simulation: Simulation = Simulation(
            day_span=[0],
            # min_profit=[1, 3, 5, 10, 20, 30, 40, 50, 70, 80, 100, 150, 200, 300, 400, 500],
            min_profit=[0.5, 20],
            history_days=365,
            threads=options["threads"],
        )
        simulation.run_simulation()
