from django.contrib import admin

from .models import (
    OHLCV,
    Account,
    Bot,
    Currency,
    Market,
    Order,
    OrderErrorLog,
    Saving,
    Trade,
)


class BotInline(admin.TabularInline):
    model = Bot
    extra = 0


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0


class TradeInline(admin.TabularInline):
    model = Trade
    extra = 0


class ErrorInline(admin.TabularInline):
    model = OrderErrorLog
    extra = 0


class SavingInline(admin.TabularInline):
    model = Saving
    extra = 0


class AccountAdmin(admin.ModelAdmin):
    fieldsets = [
        ("User", {"fields": ["user"]}),
        (
            "Exchange information",
            {"fields": ["exchange", "api_key", "secret", "password", "default_fee_rate"]},
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
    readonly_fields = (
        "created",
        "start_amount",
        "current_amount",
        "estimate_current_amount",
        "roi",
        "estimate_roi",
        "orders_count",
    )

    fieldsets = [
        ("Base", {"fields": ["account", "active"]}),
        ("Trade Mode: Wave Rider", {"fields": ["market", "timeframe"]}),
        (
            "Trade Mode: Rising Chart",
            {"fields": ["quote", "max_amount", "min_rise", "stop_loss"]},
        ),
        (
            "Stats",
            {
                "fields": [
                    "start_amount",
                    "current_amount",
                    "estimate_current_amount",
                    "roi",
                    "estimate_roi",
                    "orders_count",
                ]
            },
        ),
    ]

    list_display = (
        "account",
        "market",
        "created",
        "timeframe",
        "active",
        "roi",
        "estimate_roi",
        "orders_count",
    )
    list_filter = ["account", "timeframe", "active"]
    search_fields = ["account", "market", "created"]

    inlines = [OrderInline, SavingInline]


class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ("errors",)

    fieldsets = [
        ("Base", {"fields": ["bot", "errors"]}),
        (
            "Order",
            {
                "fields": [
                    "next_order",
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
        ("Fee", {"fields": ["fee_currency", "fee_cost", "fee_rate"]}),
        ("Rising Chart", {"fields": ["last_price_tick", "market"]}),
    ]

    list_display = (
        "next_order",
        "order_id",
        "bot",
        "timestamp",
        "status",
        "side",
        "price",
        "errors",
    )
    list_filter = ["bot", "timestamp", "status", "side"]
    search_fields = [
        "bot",
        "order_id",
        "timestamp",
        "status",
        "order_type",
        "side",
        "price",
        "amount",
        "filled",
    ]

    # inlines = [TradeInline]
    inlines = [ErrorInline]


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
