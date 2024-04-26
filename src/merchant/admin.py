from django.contrib import admin

from merchant.models import Merchant, Customer, CustomerMerchant, ApiKey

admin.site.register(ApiKey)
admin.site.register(Merchant)
admin.site.register(Customer)
admin.site.register(CustomerMerchant)
