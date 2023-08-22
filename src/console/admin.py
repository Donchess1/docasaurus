from django.contrib import admin

from console.models.transaction import Transaction, EscrowMeta, LockedAmount

admin.site.register(Transaction)
admin.site.register(EscrowMeta)
admin.site.register(LockedAmount)
