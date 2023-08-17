from django.contrib import admin

from console.models.transaction import Transaction, EscrowMeta

admin.site.register(Transaction)
admin.site.register(EscrowMeta)
