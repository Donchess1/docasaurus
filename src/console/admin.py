from django.contrib import admin

from console.models.transaction import Transaction, EscrowMeta, LockedAmount
from console.models.dispute import Dispute

admin.site.register(Transaction)
admin.site.register(EscrowMeta)
admin.site.register(LockedAmount)
admin.site.register(Dispute)
