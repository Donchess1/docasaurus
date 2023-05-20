from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from common.serializers.wallet import FundWalletSerializer
from core.resources.flutterwave import FlwAPI
from utils.response import Response
from utils.utils import calculate_payment_amount_to_charge, generate_txn_reference

User = get_user_model()


class FundWalletView(GenericAPIView):
    serializer_class = FundWalletSerializer
    permission_classes = [IsAuthenticated]
    flw_api = FlwAPI

    @swagger_auto_schema(
        operation_description="Fund user wallet",
        # responses={
        #     200: ValidatedBVNPayloadSerializer,
        # },
    )
    def post(self, request):
        user_id = request.user.id
        user = User.objects.get(id=user_id)

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        data = serializer.validated_data
        amount = data.get("amount", None)

        # amount = calculate_payment_amount_to_charge(tmp_amount)
        tx_ref = generate_txn_reference()
        email = user.email

        tx_data = {
            "tx_ref": tx_ref,
            "amount": amount,
            "email": user.email,
            "fullname": user.name,
            "phone_number": user.phone,
            "currency": "NGN",
            "narration": "MyBalance",
            "is_permanent": False,
        }

        obj = self.flw_api.initiate_bank_transfer(tx_data)
        print("VIEW", obj)
        if obj["status"] == "error":
            return Response(
                success=False,
                status_code=status.HTTP_400_BAD_REQUEST,
                message=obj["message"],
            )
        # {
        #     "status": "success",
        #     "message": "Charge initiated",
        #     "meta": {
        #         "authorization": {
        #             "transfer_reference": "MockFLWRef-1684482552934",
        #             "transfer_account": "0067100155",
        #             "transfer_bank": "Mock Bank",
        #             "account_expiration": 1684482552934,
        #             "transfer_note": "Mock note",
        #             "transfer_amount": "5000.00",
        #             "mode": "banktransfer",
        #         }
        #     },
        #     "status_code": 200,
        # }

        meta = obj["meta"]["authorization"]

        payload = {
            "amount": meta["transfer_amount"],
            "account_number": meta["transfer_account"],
            "bank_name": meta["transfer_bank"],
        }

        return Response(
            success=True,
            message="Please make a bank transfer to MyBalance with details provided.",
            status_code=status.HTTP_200_OK,
            data=payload,
        )
