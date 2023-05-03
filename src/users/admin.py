from django.contrib import admin
from django.contrib.auth import get_user_model

# from users.models.bank_account import BankAccount
# from users.models.kyc import UserKYC
# from users.models.profile import UserProfile


User = get_user_model()

admin.site.register(User)
# admin.site.register(UserKYC)
# admin.site.register(UserProfile)
# admin.site.register(BankAccount)
