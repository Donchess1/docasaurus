from rest_framework import generics, permissions, status

from users.models.bank_account import BankAccount
from users.serializers.bank_account import BankAccountSerializer
from utils.response import Response


class UserBankAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user_id=self.request.user)

    def perform_create(self, serializer):
        return serializer.save()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
            },
        )
        if not serializer.is_valid():
            return Response(
                success=False,
                message="Validation error",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = self.perform_create(serializer)
        return Response(
            success=True,
            status_code=status.HTTP_201_CREATED,
            message="Bank account created successfully",
            data=BankAccountSerializer(data).data,
        )

    def get(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = BankAccountSerializer(data, many=True)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Bank accounts retrieved successfully",
            data=serializer.data,
        )


class UserBankAccountRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        is_default = serializer.validated_data.get("is_default", False)
        user = self.request.user

        if is_default:
            BankAccount.objects.filter(user_id=user).update(is_default=False)
        serializer.save()

    def patch(self, request, id, *args, **kwargs):
        instance = BankAccount.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Bank account does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.user_id != self.request.user:
            return Response(
                success=False,
                message="Unable to retrieve bank account. Permission denied.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        is_default = self.request.data.get("is_default", False)
        if is_default:
            BankAccount.objects.filter(user_id=self.request.user).update(
                is_default=False
            )
            instance.is_default = True
            instance.save()

        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Bank account updated successfully",
            data=serializer.data,
        )

    def get(self, request, id, *args, **kwargs):
        instance = BankAccount.objects.filter(id=id).first()
        if not instance:
            return Response(
                success=False,
                message="Bank account does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if instance.user_id != self.request.user:
            return Response(
                success=False,
                message="Unable to retrieve bank account. Permission denied.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance)
        return Response(
            success=True,
            status_code=status.HTTP_200_OK,
            message="Bank account retrieved successfully",
            data=serializer.data,
        )
