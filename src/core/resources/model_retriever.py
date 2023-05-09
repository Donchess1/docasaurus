from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status

from business.models.business import Business
from users.models.bank_account import BankAccount
from users.models.kyc import UserKYC
from users.models.profile import UserProfile

User = get_user_model()

MODEL_REGISTRY = {
    "BankAccount": BankAccount,
    "Business": Business,
    "User": User,
    "UserKYC": UserKYC,
    "UserProfile": UserProfile,
}


class ModelRetriever:
    @classmethod
    def get_object(cls, model_name, id):
        model = MODEL_REGISTRY[model_name]
        try:
            obj = model.objects.get(id=id)
        except model.DoesNotExist:
            return None
        return obj
