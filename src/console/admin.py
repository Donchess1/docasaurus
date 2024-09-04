from django.contrib import admin

from console.models import (
    Transaction,
    EscrowMeta,
    LockedAmount,
    Dispute,
    NINIdentity,
    Product,
    Event,
    TicketPurchase,
    EmailLog,
    SystemConfig,
)

admin.site.register(Transaction)
admin.site.register(EscrowMeta)
admin.site.register(LockedAmount)
admin.site.register(Dispute)
admin.site.register(NINIdentity)
admin.site.register(EmailLog)
admin.site.register(SystemConfig)
admin.site.register(Event)
admin.site.register(Product)
admin.site.register(TicketPurchase)
