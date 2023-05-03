# from django.contrib.auth import get_user_model
# from django.db import models

# from business.models.business import Business

# from .kyc import UserKYC

# # from users.models.user import User
# User = get_user_model()


# class UserProfile(models.Model):
#     user_id = user_id = models.OneToOneField(User, on_delete=models.CASCADE)
#     kyc_id = models.ForeignKey(
#         UserKYC, on_delete=models.SET_NULL, null=True, blank=True
#     )
#     business_id = models.ForeignKey(
#         Business, on_delete=models.SET_NULL, null=True, blank=True
#     )
#     avatar = models.URLField(null=True, blank=True)
#     profile_link = models.URLField(null=True, blank=True)
#     wallet_balance = models.IntegerField(default=0, null=True, blank=True)
#     locked_amount = models.IntegerField(default=0, null=True, blank=True)
#     unlocked_amount = models.IntegerField(default=0, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.email
