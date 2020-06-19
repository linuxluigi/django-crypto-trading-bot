from django.contrib import admin

from .models import OHLCV, Account, Bot, Currency, Market, Order, Trade


class BotInline(admin.TabularInline):
    model = Bot
    extra = 0


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0


class TradeInline(admin.TabularInline):
    model = Trade
    extra = 0


class AccountAdmin(admin.ModelAdmin):
    fieldsets = [
        ("User", {"fields": ["user"]}),
        (
            "Exchange information",
            {"fields": ["exchange", "api_key", "secret", "password"]},
        ),
    ]

    list_display = ("user", "exchange")
    list_filter = ["user", "exchange"]
    search_fields = ["user"]

    inlines = [BotInline]


class CurrencyAdmin(admin.ModelAdmin):
    fields = ["short", "name"]

    list_display = ("short", "name")
    search_fields = ["short", "name"]


class MarketAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Base", {"fields": ["exchange", "active"]}),
        ("Currencies", {"fields": ["base", "quote"]}),
        (
            "Market information",
            {
                "classes": ("collapse",),
                "fields": [
                    "precision_amount",
                    "precision_price",
                    "limits_amount_min",
                    "limits_amount_max",
                    "limits_price_min",
                    "limits_price_max",
                ],
            },
        ),
    ]

    list_display = ("symbol", "exchange", "active")
    list_filter = ["exchange", "active"]
    search_fields = ["base", "quote"]


class BotAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Base", {"fields": ["account", "market"]}),
        ("Settings", {"fields": ["timeframe"]}),
    ]

    readonly_fields = ("created",)

    list_display = ("account", "market", "created", "timeframe")
    list_filter = ["account", "timeframe"]
    search_fields = ["account", "market", "created"]

    inlines = [OrderInline]


class OrderAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Base", {"fields": ["bot", "exchange"]}),
        (
            "Order",
            {
                "fields": [
                    "order_id",
                    "timestamp",
                    "status",
                    "order_type",
                    "side",
                    "price",
                    "amount",
                    "filled",
                ]
            },
        ),
    ]

    list_display = (
        "order_id",
        "bot",
        "exchange",
        "timestamp",
        "status",
        "side",
        "price",
    )
    list_filter = ["bot", "exchange", "timestamp", "status", "side"]
    search_fields = [
        "bot",
        "order_id",
        "timestamp",
        "status",
        "exchange",
        "order_type",
        "side",
        "price",
        "amount",
        "filled",
    ]

    # inlines = [TradeInline]


class TradeAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "order",
                    "trade_id",
                    "timestamp",
                    "taker_or_maker",
                    "amount",
                    "fee_currency",
                    "fee_cost",
                    "fee_rate",
                ]
            },
        ),
    ]

    list_display = (
        "order",
        "trade_id",
        "timestamp",
        "taker_or_maker",
        "amount",
        "fee_rate",
    )
    list_filter = ["taker_or_maker", "timestamp"]
    search_fields = [
        "order",
        "trade_id",
        "timestamp",
        "taker_or_maker",
        "amount",
        "fee_currency",
        "fee_cost",
        "fee_rate",
    ]


class OHLCVAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "market",
                    "timeframe",
                    "timestamp",
                    "open_price",
                    "highest_price",
                    "lowest_price",
                    "closing_price",
                    "volume",
                ]
            },
        ),
    ]

    list_display = (
        "market",
        "timeframe",
        "timestamp",
        "open_price",
        "highest_price",
        "lowest_price",
        "closing_price",
        "volume",
    )
    list_filter = ["market", "timeframe", "timestamp"]
    search_fields = [
        "market",
        "timeframe",
        "timestamp",
        "open_price",
        "highest_price",
        "lowest_price",
        "closing_price",
        "volume",
    ]


admin.site.register(Account, AccountAdmin)
admin.site.register(Bot, BotAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Market, MarketAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Trade, TradeAdmin)
admin.site.register(OHLCV, OHLCVAdmin)
