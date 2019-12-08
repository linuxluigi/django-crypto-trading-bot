from factory import DjangoModelFactory, Faker, post_generation, SubFactory
from typing import Any, Sequence
from django_crypto_trading_bot.users.models import User
from django_crypto_trading_bot.users.tests.factories import UserFactory
from config.settings.base import env
import pytest



class AccountFactory(DjangoModelFactory):
    class Meta:
        model = "trading_bot.Account"
        django_get_or_create = [
            "api_key",
        ]

    exchange = "kucoin"
    user = SubFactory(UserFactory)
    api_key = env("KUCOIN_SANDBOX_PUBLIC_KEY")
    secret = env("KUCOIN_SANDBOX_PRIVATE_KEY")
    password = env("KUCOIN_SANDBOX_PASSWORD")
    sandbox = True

